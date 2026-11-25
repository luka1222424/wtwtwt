"""Run ESP32 UART logging and camera/ONNX processing on Raspberry Pi."""

import argparse
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import signal
import subprocess
import threading
import time
import uuid

from .camera_capture import CameraCapture, timestamped_image_path
from .leaf_worker_client import LeafWorkerClient
from .serial_protocol import DEFAULT_SERIAL_DEVICE, UART_BAUD_RATE, SerialProtocolError, parse_serial_line
from .storage import EventLogger, MeasurementCsvLogger


class ExperimentRunner:
    def __init__(self, args):
        self.args = args
        self.mode = args.mode.upper()
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
        self.events = EventLogger(args.events_log)
        self.measurements = MeasurementCsvLogger(args.measurements_csv)
        self.camera = CameraCapture()
        self.classifier = None
        self.stop_event = threading.Event()
        self.cancelled = threading.Event()
        self.camera_cycle_success = None
        self.camera_cycle_complete = threading.Event()

    def stop(self):
        self.stop_event.set()

    def cancel(self):
        self.cancelled.set()
        self.stop()

    def log(self, event_type, **details):
        return self.events.log_event(event_type, run_id=self.run_id, operating_mode=self.mode, **details)

    def read_uart(self):
        try:
            import serial
        except ImportError:
            self.log("serial_error", error="Install pyserial")
            self.stop()
            return
        previous_sequence = None
        while not self.stop_event.is_set():
            try:
                with serial.Serial(self.args.serial_device, UART_BAUD_RATE, timeout=0.5) as port:
                    self.log("serial_connected", serial_device=self.args.serial_device)
                    while not self.stop_event.is_set():
                        try:
                            data = parse_serial_line(port.readline())
                        except SerialProtocolError as error:
                            self.log("serial_protocol_error", error=str(error))
                            continue
                        if data is None:
                            continue
                        if data["mode"] != self.mode:
                            self.log("mode_mismatch", received_mode=data["mode"])
                            continue
                        if self.mode == "BASELINE" and previous_sequence is not None and data["sequence"] != previous_sequence + 1:
                            self.log("serial_sequence_gap", previous=previous_sequence, received=data["sequence"])
                        previous_sequence = data["sequence"]
                        payload = {**data, "run_id": self.run_id}
                        timestamp = self.events.log_measurement(payload, f"serial:{self.args.serial_device}")
                        self.measurements.log(payload, timestamp)
            except Exception as error:
                # Reconnect if the cable/serial device temporarily disappears.
                self.log("serial_error", error=str(error))
                self.stop_event.wait(2)

    def _start_classifier(self):
        self.classifier = LeafWorkerClient(self.args.onnx_python, self.args.leaf_worker)
        metadata = self.classifier.start()
        self.log("leaf_model_loaded", provider=metadata["providers"], model_load_count=metadata["model_load_count"])

    def capture_and_classify(self):
        image_path = timestamped_image_path(self.args.image_dir)
        self.log("camera_capture_started", image_path=str(image_path))
        try:
            capture = self.camera.capture(image_path)
            self.log("camera_capture", status="success", image_path=str(image_path),
                     capture_backend=capture.backend, duration_seconds=capture.capture_time_ms / 1000)
        except Exception as error:
            self.log("camera_capture", status="failed", error=str(error))
            return False
        started = time.monotonic()
        try:
            if self.mode == "BASELINE" and not self.classifier.is_running:
                self.log("leaf_worker_restarting")
                self.classifier.stop()
                self._start_classifier()
            result = self.classifier.classify(image_path)
            self.log("camera_processing", status="success", image_path=str(image_path),
                     duration_seconds=time.monotonic() - started,
                     condition=result["condition"], healthy_score=result["healthy_score"],
                     unhealthy_score=result["unhealthy_score"],
                     inference_time_ms=result["inference_time_ms"])
            print(f"{image_path.name}: {result['condition']} (healthy={result['healthy_score']:.3f})", flush=True)
            return True
        except Exception as error:
            self.log("camera_processing", status="failed", error=str(error))
            return False

    def camera_loop(self):
        if self.mode == "OPTIMIZED":
            try:
                self.camera_cycle_success = self.capture_and_classify()
            finally:
                self.camera_cycle_complete.set()
                if self.args.shutdown_after_initial_cycle:
                    self.stop()
            return
        next_capture = time.monotonic()
        while not self.stop_event.is_set():
            if self.stop_event.wait(max(0, next_capture - time.monotonic())):
                break
            self.capture_and_classify()
            next_capture += self.args.camera_interval_seconds
            # Do not execute a burst of overdue captures after a long failure.
            if next_capture <= time.monotonic():
                next_capture = time.monotonic() + self.args.camera_interval_seconds

    def _poweroff(self):
        self.log("pi_poweroff_requested", cycle_success=self.camera_cycle_success)
        try:
            # Flush application logs/images before asking systemd to halt.
            os.sync()
            subprocess.run(["sudo", "-n", "/usr/bin/systemctl", "poweroff"],
                           check=True, timeout=10)
        except Exception as error:
            self.log("pi_poweroff_failed", error=str(error))
            return False
        return True

    def run(self):
        self.log("run_started", mode=self.mode)
        serial_thread = None
        camera_thread = None
        failure = None
        auto_halt = self.mode == "OPTIMIZED" and self.args.shutdown_after_initial_cycle
        try:
            self._start_classifier()
            camera_status = self.camera.detect()
            self.log("camera_detection", status="available" if camera_status.available else "unavailable")
            print(f"RUN_MARKER run_id={self.run_id} mode={self.mode}", flush=True)
            serial_thread = threading.Thread(target=self.read_uart, daemon=True)
            camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            serial_thread.start()
            camera_thread.start()
            if self.args.duration_seconds:
                self.stop_event.wait(self.args.duration_seconds)
            else:
                while not self.stop_event.wait(0.5):
                    pass
        except Exception as error:
            failure = error
            self.log("run_failed", error=str(error))
        finally:
            self.stop()
            if serial_thread is not None:
                serial_thread.join(timeout=3)
            if camera_thread is not None:
                camera_thread.join(timeout=95)
            # Never contend for the worker lock if a camera thread is stuck.
            if camera_thread is not None and camera_thread.is_alive():
                self.log("camera_thread_timeout")
                failure = failure or RuntimeError("camera thread did not stop")
            elif self.classifier is not None:
                try:
                    self.classifier.stop()
                except Exception as error:
                    self.log("worker_cleanup_failed", error=str(error))
                    failure = failure or error
            self.log("run_stopped", cycle_success=self.camera_cycle_success,
                     camera_cycle_complete=self.camera_cycle_complete.is_set())
            print(f"RUN_COMPLETE run_id={self.run_id}", flush=True)

        # On a failed image/model cycle, log the failure and halt as well so
        # the next scheduled GPIO wake can recover. Never halt a cancelled
        # experiment or a manually stopped service merely because it stopped.
        if auto_halt and not self.cancelled.is_set() and (self.camera_cycle_complete.is_set() or failure is not None):
            if self.camera_cycle_success is not True:
                self.log("optimized_cycle_failed", reason="camera_or_model_failure")
            return 0 if self._poweroff() else 1
        return 1 if failure is not None else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["baseline", "optimized"])
    parser.add_argument("--serial-device", default=DEFAULT_SERIAL_DEVICE)
    parser.add_argument("--events-log", type=Path, default=Path("events_log.txt"))
    parser.add_argument("--measurements-csv", type=Path, default=Path("test_events.csv"))
    parser.add_argument("--image-dir", type=Path, default=Path("images"))
    parser.add_argument("--onnx-python", type=Path, default=Path(".venv-onnx/bin/python"))
    parser.add_argument("--leaf-worker", type=Path, default=Path("leaf_classifier/worker.py"))
    parser.add_argument("--camera-interval-seconds", type=float, default=1800)
    parser.add_argument("--duration-seconds", type=float, default=0)
    parser.add_argument("--shutdown-after-initial-cycle", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.camera_interval_seconds) or not math.isfinite(args.duration_seconds) or args.camera_interval_seconds <= 0 or args.duration_seconds < 0:
        parser.error("invalid interval or duration")
    if args.mode == "baseline" and args.shutdown_after_initial_cycle:
        parser.error("shutdown-after-initial-cycle is only available in optimized mode")
    # The public optimized CLI always follows the production HALT path.
    if args.mode == "optimized":
        args.shutdown_after_initial_cycle = True
    runner = ExperimentRunner(args)
    signal.signal(signal.SIGINT, lambda *_: runner.cancel())
    signal.signal(signal.SIGTERM, lambda *_: runner.cancel())
    # Linux/Pi: serialize direct and systemd launches for the same project.
    import fcntl
    with Path(".smartplant.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("another Smart Plant runner already holds the project lock")
        raise SystemExit(runner.run())


if __name__ == "__main__":
    main()
