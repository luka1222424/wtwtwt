# Deployment validation (no new energy measurements)

## Current evidence (25 November 2026)

See [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md). Shared calibration defaults reproduce the tested sensor (1246/2390); recalibrate for other hardware. Production test supports normal/event-triggered wake and poweroff requests, but stable mode and exact physical HALT durations remain unverified. Post-integration 36 tests passed and 4 were skipped locally; check CI separately.

## Release gate

- Host policy test: compile the exact C header via `python -m unittest discover -s tests -p test_camera_policy.py -v` in raspberry_pi.
- Full Python suite: from raspberry_pi, use the ONNX virtual environment or CI after installing the exact dependencies and downloading the hash-verified model. Camera/Pi poweroff tests use mocks; actual camera and GPIO are NOT covered.
- Bash syntax: `for script in raspberry_pi/*.sh; do bash -n "$script" || exit 1; done` from repo root.
- Both ESP-IDF 6.1 builds: use separate fresh sdkconfig and build directories as documented in README.
- Physical checks below are required even when CI is green.

## Raspberry Pi preparation

1. Raspberry Pi 4B, Raspberry Pi OS Bookworm 64-bit, Python 3.11, apt packages python3-venv python3-picamera2 python3-numpy python3-pil and Internet for the first install (model and pip dependencies). No new Monsoon measurements.
2. Verify /dev/serial0, serial console disabled, common ground, GPIO26 open-drain connection to Pi GPIO3, EEPROM WAKE_ON_GPIO=1 and POWER_OFF_ON_HALT=0; gpio-shutdown overlay disabled. Verify power/wiring before energizing boards.
3. From raspberry_pi: run ./prepare_raspberry_pi.sh then ./check_raspberry_pi.sh --serial. Use `--baseline` or `--optimized` to enforce the flashed mode, 20 s interval, and valid calibrated sensor readings. The preflight checks a real photo and its ONNX inference as well as bundled test images. Do not run while another camera/UART process owns those resources.
4. Set physically measured dry and wet ADC endpoints and enable soil calibration in the active ESP32 config. Default thresholds are RH > 50%, temperature < 15 C, soil < 300/1000. For a stable test, no rule may be active: RH <= 50%, temperature >= 15 C, soil >= 300/1000. Otherwise 120-min stability is correctly disallowed. A DHT error also blocks the stable transition.
5. BASELINE: disable autonomous service with sudo systemctl disable --now smartplant-optimized.service if previously installed, flash fresh BASELINE build, run ./run_baseline.sh. Verify RUN_MARKER, serial records and images. Stop via ./stop_test.sh before switching modes.
6. OPTIMIZED: flash fresh OPTIMIZED firmware, install service using ./install_optimized_power_service.sh, reboot once. Record console logs with host timestamps; verify each Pi wake, capture/inference and halt. Capture events_log.txt, test_events.csv and images. A GPIO pulse is only a request, not proof of actual wake; the Pi cannot receive UART when halted.
7. For fast functional tests use a separately named build with 6/18 cycles instead of 90/360 (allow Pi to complete boot/capture/halt before the next request; extend further if necessary); leave 20 s sensor cadence unchanged. Use baseline CAMERA_INTERVAL_SECONDS=60 only as a labelled test override. See [LAB_RUNBOOK.md](LAB_RUNBOOK.md) for explicit commands and evidence archiving. Restore production defaults afterwards. Exercise stable, new alarm, persistent alarm and recovery. An alarm detected while the Pi is already active is not guaranteed to generate an additional image.
8. When an optimized capture/model attempt fails, logs now record failure and the Pi attempts orderly halt after cleanup to permit future wakes. No failed attempt is counted as a successful inference. If poweroff itself fails, service retries at most within its configured start-rate limit; repeated errors need intervention. Check journalctl -u smartplant-optimized.service and power state. Reinstall service after updating its template. For log retrieval after a verified HALT, the FAT boot partition smartplant-maintenance marker suppresses auto-start on the next boot; follow LAB_RUNBOOK.md.

## Evidence and limitations

The GitHub workflow compiles both firmware profiles and runs host and model tests if GitHub Actions is available. Its result must be inspected, not inferred from the presence of this file. The actual sensor calibration, Pi EEPROM, UART, camera, poweroff and wake wiring need physical checks. No guarantee of hardware operation without these checks; no new energy measurements are required for functional validation. The energy projection is conditional on historical coefficients and separate from actual device testing.
