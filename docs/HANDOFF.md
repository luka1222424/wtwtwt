# Smart Plant — complete technical handoff

> **Current release:** See [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md) for the new physical evidence and updated projections. Historical extraction and audit are retained separately.

Start here. This public repository contains the complete active implementation. Both firmware modes share one ESP32 source tree and use distinct build configurations. Read only unless explicitly instructed to change something. Do not redesign the project or invent evidence.

## 1. Get all required files

```bash
git clone https://github.com/luka1222424/wtwtwt.git
cd wtwtwt
git rev-parse HEAD
```

Alternatively download the repository ZIP. Preserve the directory structure. Copy the complete esp32/ directory to the ESP-IDF workstation and complete raspberry_pi/ directory to Raspberry Pi; a complete checkout on both is preferred.

| Files | Purpose |
|---|---|
| [esp32/](../esp32/) | Complete ESP32 project, both profiles |
| [main.c](../esp32/main/main.c) | Sampling, alarms, RTC state, mode selection and deep sleep |
| [camera_policy.h](../esp32/main/camera_policy.h) | Adaptive camera wake policy |
| [measurement_output.c](../esp32/main/measurement_output.c), [header](../esp32/main/measurement_output.h) | UART and mirrored USB evidence |
| [raspberry_pi_wake.c](../esp32/main/raspberry_pi_wake.c), [header](../esp32/main/raspberry_pi_wake.h) | GPIO wake |
| [dht11.c](../esp32/main/dht11.c), [header](../esp32/main/dht11.h) | Air sensor driver |
| [components/](../esp32/components/) | Complete buzzer, monitoring, soil moisture components and headers |
| [CMakeLists.txt](../esp32/CMakeLists.txt), [main CMakeLists](../esp32/main/CMakeLists.txt), [Kconfig](../esp32/main/Kconfig.projbuild) | Build and configuration |
| [shared defaults](../esp32/sdkconfig.defaults), [BASELINE](../esp32/sdkconfig.baseline.defaults), [OPTIMIZED](../esp32/sdkconfig.optimized.defaults) | Firmware profiles |
| [configuration.txt](../esp32/config/configuration.txt) | Alarm thresholds |
| [raspberry_pi/](../raspberry_pi/) | Complete Raspberry Pi project |
| [prepare_raspberry_pi.sh](../raspberry_pi/prepare_raspberry_pi.sh) | Install runtime dependencies and pinned ONNX model |
| [check_raspberry_pi.sh](../raspberry_pi/check_raspberry_pi.sh) | Camera/model/UART preflight |
| [run_baseline.sh](../raspberry_pi/run_baseline.sh), [run_optimized.sh](../raspberry_pi/run_optimized.sh), [run_test.sh](../raspberry_pi/run_test.sh), [stop_test.sh](../raspberry_pi/stop_test.sh) | Launch and stop scripts |
| [install_optimized_power_service.sh](../raspberry_pi/install_optimized_power_service.sh), [systemd service](../raspberry_pi/systemd/smartplant-optimized.service) | Autonomous one-cycle boot service |
| [smartplant_pi/](../raspberry_pi/smartplant_pi/) | All runtime Python modules: experiment_runner.py, camera_capture.py, leaf_worker_client.py, serial_protocol.py, storage.py, __init__.py |
| [leaf_classifier/](../raspberry_pi/leaf_classifier/) | All classifier modules, ordered labels, requirements, manifest, licenses and four reference images |
| [requirements-camera.txt](../raspberry_pi/requirements-camera.txt) | Camera/UART requirements |
| [tests/](../raspberry_pi/tests/) | Full automated regression suite |
| [project_energy.py](../raspberry_pi/project_energy.py) | Energy projection, not measurement |
| [CI workflow](../.github/workflows/smartplant-validation.yml) | Both firmware builds and host/model validation |

External model.onnx is not tracked. The prepare script downloads the pinned external model and verifies its SHA-256 from [ASSETS.json](../raspberry_pi/leaf_classifier/ASSETS.json). Preserve model and dataset attribution, licenses, image fixtures and ordered labels. No paid API required.

## 2. Required behaviour

| Parameter | BASELINE | OPTIMIZED |
|---|---|---|
| Temperature, air humidity, soil moisture | 20 s nominal; ESP32 continuously awake | 20 s deep sleep plus awake overhead |
| Camera and ONNX | Startup then every 1800 s | One attempt per Pi boot; 90 cycles (~30 min) normal; 360 (~120 min) stable |
| New environmental alarm or actual sensor fault | Local alarm | Immediate GPIO wake request at detecting sample |
| Persistent alarm | Local alarm | No wake every sample; normal schedule |
| Pi | Continuously running | Orderly halt after successful or failed processing attempt; remains electrically powered |

Stable policy needs at least one prior wake request and 90 consecutive valid alarm-free samples. Invalid calibration prevents stability. No Pi acknowledgement exists: GPIO success is not proof of boot or image capture. A pulse while Pi is active may not cause another image. Visual-only disease cannot be detected by environmental sensors between captures. Both modes have comparable nominal environmental sensing; discuss effective overhead and visual latency trade-off. See [adaptive scenario](ADAPTIVE_SCENARIO.md).

## 3. Hardware, build and execution

Read [LAB_RUNBOOK.md](LAB_RUNBOOK.md) and [WIRING.md](../esp32/docs/WIRING.md) before touching hardware. ESP32-WROOM-32, Pi 4B, CSI camera, DHT11, analog soil sensor, passive buzzer. Disconnect both supplies before wiring. ESP GPIO4 DHT11, GPIO34 soil AO, GPIO25 buzzer; TX17 to Pi RX15 physical pin 10, RX16 to Pi TX14 pin 8, GPIO26 open-drain to Pi GPIO3 pin 5, common ground pin 6. 3.3 V logic, never 5 V to ESP GPIO. Wake pulse 250 ms LOW. UART 115200 8N1 /dev/serial0, serial hardware enabled and login disabled. EEPROM WAKE_ON_GPIO=1, POWER_OFF_ON_HALT=0, no gpio-shutdown overlay. Keep Pi supply connected after HALT. Physically measure distinct dry/wet calibration endpoints, apply identical values to both profiles; no invented calibration. Stable thresholds: RH <=50%, temperature >=15 C, soil >=300/1000, valid readings.

ESP-IDF 6.1 PowerShell, from esp32/ (replace COM4):
```powershell
idf.py -B build-baseline -D "SDKCONFIG=sdkconfig.baseline" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.baseline.defaults" reconfigure
idf.py -B build-baseline -D "SDKCONFIG=sdkconfig.baseline" menuconfig
idf.py -B build-baseline -D "SDKCONFIG=sdkconfig.baseline" -p COM4 build flash monitor
idf.py -B build-optimized -D "SDKCONFIG=sdkconfig.optimized" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.optimized.defaults" reconfigure
idf.py -B build-optimized -D "SDKCONFIG=sdkconfig.optimized" menuconfig
idf.py -B build-optimized -D "SDKCONFIG=sdkconfig.optimized" -p COM4 build flash monitor
```
Flash one at a time, exit monitor before switching. Set measured calibration in menuconfig. Final optimized 20s/90/360, baseline camera 1800s.

Pi OS Bookworm 64-bit, Python 3.11. From repository root:
```bash
sudo apt update
sudo apt install -y python3-venv python3-picamera2 python3-numpy python3-pil
cd raspberry_pi
chmod +x ./*.sh
./prepare_raspberry_pi.sh
./check_raspberry_pi.sh
```
BASELINE after calibrated baseline flash:
```bash
# If previously installed:
sudo systemctl disable --now smartplant-optimized.service
./check_raspberry_pi.sh --baseline
./run_baseline.sh
tail -f runtime_baseline.log
# In separate terminal when finished:
./stop_test.sh
```
OPTIMIZED after stopping baseline and calibrated optimized flash:
```bash
./check_raspberry_pi.sh --optimized
./install_optimized_power_service.sh
sudo rm -f /boot/firmware/smartplant-maintenance
sudo reboot
```
Do not run direct launcher alongside service. Manual initial boot is not ESP-triggered. Optimized always requests HALT after its production cycle.

## 4. Functional tests and evidence

The hardware-tested runtime revision passed all 40 tests and both firmware builds in [CI run 45693380177](https://github.com/luka1222424/wtwtwt/actions/runs/45693380177). Current release restricts the optimized launcher to the same HALT-enabled path; inspect current CI separately. Production evidence supports normal/event-driven operation; stable 360-cycle operation is untested physically. See CURRENT_EVALUATION.md.

Use the production intervals for both profiles. Follow the runbook for maintenance and evidence retrieval.

Record ESP USB console with host timestamps (SMARTPLANT_JSON, CAMERA_POLICY, PI_WAKE_REQUEST), Pi events_log.txt, test_events.csv, images/, runtime_baseline.log, runtime_optimized.log, systemd journal. Archive separately with commit, calibration, intervals and observed actual wake/halt. Pi cannot log while halted. A wake request is not a successful capture. Do not invent missing measurements or logs.

## 5. Energy model and report

Read [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md). Current 144 h projection: BASELINE 264.866 Wh, adaptive 194.547 Wh (26.5488%). Run `python evaluation/analyze_current.py` from repository root after installing evaluation requirements. For arbitrary activity counts use `python raspberry_pi/project_energy.py --pi-blocks 109`. Historical power coefficients and new cadence are separate; no fresh electrical measurement is claimed.

## 6. AI review task

Read only. Use existing validation, avoid repeating expensive tests unless investigating a concrete blocker. Do not refactor, redesign, change hardware or introduce optional optimizations. Return only: specification PASS/FAIL; deployment readiness PASS/FAIL; actual critical blockers with file/line or none; GO/NO-GO for physical testing. Physical validation supports normal/event-triggered cycles; see current evidence and remaining limitations.
