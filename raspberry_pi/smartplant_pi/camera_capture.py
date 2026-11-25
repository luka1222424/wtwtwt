"""Real Raspberry Pi CSI camera detection and still-image capture."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import importlib
from pathlib import Path
import shlex
import shutil
import subprocess
import time
from typing import Any


DEFAULT_CAMERA_COMMAND = (
    "rpicam-still --nopreview --timeout {warmup_ms} --camera {camera} "
    "--width {width} --height {height} --output {output}"
)


class CameraUnavailableError(RuntimeError):
    """Raised when neither Picamera2 nor rpicam can see a real camera."""


class CameraCaptureError(RuntimeError):
    """Raised when a detected camera fails to produce an image."""


@dataclass(frozen=True)
class CameraStatus:
    available: bool
    backend: str | None
    camera_count: int
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaptureResult:
    image_path: Path
    captured_at: str
    backend: str
    camera_index: int
    capture_time_ms: float


def timestamped_image_path(output_dir: Path, prefix: str = "plant") -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    return output_dir / f"{prefix}_{stamp}.jpg"


def build_camera_command(
    template: str,
    output_path: Path,
    camera_index: int = 0,
    width: int = 1280,
    height: int = 720,
    warmup_seconds: float = 2.0,
) -> list[str]:
    """Expand a fallback command without invoking a shell."""
    if "{output}" not in template:
        raise ValueError("camera command must contain {output}")
    replacements = {
        "{output}": str(output_path),
        "{camera}": str(camera_index),
        "{width}": str(width),
        "{height}": str(height),
        "{warmup_ms}": str(max(0, round(warmup_seconds * 1000))),
    }
    command: list[str] = []
    for token in shlex.split(template):
        for placeholder, value in replacements.items():
            token = token.replace(placeholder, value)
        command.append(token)
    if not command:
        raise ValueError("camera command is empty")
    return command


class CameraCapture:
    """Detect and capture from Picamera2, with rpicam-still fallback."""

    def __init__(
        self,
        backend: str = "auto",
        camera_index: int = 0,
        width: int = 1280,
        height: int = 720,
        warmup_seconds: float = 2.0,
        timeout_seconds: float = 30.0,
        command_template: str = DEFAULT_CAMERA_COMMAND,
    ) -> None:
        if backend not in {"auto", "picamera2", "rpicam-still"}:
            raise ValueError("unsupported camera backend")
        if camera_index < 0 or width <= 0 or height <= 0:
            raise ValueError("camera index and dimensions are invalid")
        if warmup_seconds < 0 or timeout_seconds <= 0:
            raise ValueError("camera timing is invalid")
        build_camera_command(
            command_template,
            Path("camera-check.jpg"),
            camera_index,
            width,
            height,
            warmup_seconds,
        )
        self.backend = backend
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.warmup_seconds = warmup_seconds
        self.timeout_seconds = timeout_seconds
        self.command_template = command_template

    def _picamera2_status(self) -> CameraStatus:
        try:
            module = importlib.import_module("picamera2")
            picamera2_class = module.Picamera2
            cameras = picamera2_class.global_camera_info()
        except (ImportError, AttributeError) as error:
            return CameraStatus(False, "picamera2", 0, f"Picamera2 unavailable: {error}")
        except Exception as error:
            return CameraStatus(False, "picamera2", 0, f"Picamera2 detection failed: {error}")
        count = len(cameras)
        if self.camera_index >= count:
            return CameraStatus(
                False,
                "picamera2",
                count,
                f"camera index {self.camera_index} is unavailable",
            )
        model = cameras[self.camera_index].get("Model", "unknown")
        return CameraStatus(True, "picamera2", count, f"camera {self.camera_index}: {model}")

    def _rpicam_status(self) -> CameraStatus:
        tokens = shlex.split(self.command_template)
        command_name = "rpicam-hello" if shutil.which("rpicam-hello") else tokens[0]
        executable = shutil.which(command_name)
        if executable is None:
            return CameraStatus(False, "rpicam-still", 0, "rpicam tools not found")
        try:
            result = subprocess.run(
                [executable, "--list-cameras"],
                check=False,
                capture_output=True,
                text=True,
                timeout=min(self.timeout_seconds, 10.0),
            )
        except Exception as error:
            return CameraStatus(False, "rpicam-still", 0, f"camera listing failed: {error}")
        listing = f"{result.stdout}\n{result.stderr}"
        camera_lines = [
            line for line in listing.splitlines()
            if line.lstrip()[:1].isdigit() and ":" in line
        ]
        count = len(camera_lines)
        if result.returncode != 0 or self.camera_index >= count:
            detail = listing.strip()[-300:] or "no camera reported"
            return CameraStatus(False, "rpicam-still", count, detail)
        return CameraStatus(True, "rpicam-still", count, camera_lines[self.camera_index].strip())

    def detect(self) -> CameraStatus:
        if self.backend in {"auto", "picamera2"}:
            status = self._picamera2_status()
            if status.available or self.backend == "picamera2":
                return status
        return self._rpicam_status()

    def _capture_picamera2(self, output_path: Path) -> None:
        module = importlib.import_module("picamera2")
        camera = module.Picamera2(camera_num=self.camera_index)
        started = False
        try:
            config_kwargs = {"main": {"size": (self.width, self.height)}}
            sensor_modes = getattr(camera, "sensor_modes", None) or []
            if any(m.get("size") == (2304, 1296) for m in sensor_modes):
                config_kwargs["sensor"] = {"output_size": (2304, 1296)}
            configuration = camera.create_still_configuration(**config_kwargs)
            camera.configure(configuration)
            camera.start()
            started = True
            if self.warmup_seconds:
                time.sleep(self.warmup_seconds)
            camera.capture_file(str(output_path))
        finally:
            if started:
                camera.stop()
            camera.close()

    def _capture_rpicam(self, output_path: Path) -> None:
        command = build_camera_command(
            self.command_template,
            output_path,
            self.camera_index,
            self.width,
            self.height,
            self.warmup_seconds,
        )
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        if result.returncode != 0:
            raise CameraCaptureError(
                f"rpicam-still failed with code {result.returncode}: "
                f"{result.stderr.strip()[-300:]}"
            )

    def capture(self, output_path: Path) -> CaptureResult:
        status = self.detect()
        if not status.available or status.backend is None:
            raise CameraUnavailableError(status.detail)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.unlink(missing_ok=True)
        started = time.perf_counter_ns()
        backend = status.backend
        try:
            if backend == "picamera2":
                self._capture_picamera2(output_path)
            else:
                self._capture_rpicam(output_path)
        except Exception as primary_error:
            output_path.unlink(missing_ok=True)
            if self.backend == "auto" and backend == "picamera2":
                fallback = self._rpicam_status()
                if fallback.available:
                    backend = "rpicam-still"
                    try:
                        self._capture_rpicam(output_path)
                    except Exception as fallback_error:
                        output_path.unlink(missing_ok=True)
                        raise CameraCaptureError(str(fallback_error)) from fallback_error
                else:
                    raise CameraCaptureError(str(primary_error)) from primary_error
            else:
                raise CameraCaptureError(str(primary_error)) from primary_error
        duration_ms = (time.perf_counter_ns() - started) / 1_000_000.0
        if not output_path.is_file() or output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            raise CameraCaptureError("camera returned no image file")
        return CaptureResult(
            image_path=output_path,
            captured_at=datetime.now(timezone.utc).isoformat(),
            backend=backend,
            camera_index=self.camera_index,
            capture_time_ms=duration_ms,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("images"))
    parser.add_argument("--backend", choices=("auto", "picamera2", "rpicam-still"), default="auto")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--warmup-seconds", type=float, default=2.0)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--camera-command", default=DEFAULT_CAMERA_COMMAND)
    parser.add_argument("--detect-only", action="store_true")
    arguments = parser.parse_args()
    camera = CameraCapture(
        backend=arguments.backend,
        camera_index=arguments.camera_index,
        width=arguments.width,
        height=arguments.height,
        warmup_seconds=arguments.warmup_seconds,
        timeout_seconds=arguments.timeout_seconds,
        command_template=arguments.camera_command,
    )
    status = camera.detect()
    print(status.to_dict())
    if arguments.detect_only:
        if not status.available:
            raise SystemExit(1)
        return
    if not status.available:
        raise CameraUnavailableError(status.detail)
    result = camera.capture(timestamped_image_path(arguments.output_dir))
    print(asdict(result))


if __name__ == "__main__":
    main()
