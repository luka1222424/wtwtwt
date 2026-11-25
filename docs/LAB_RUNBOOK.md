# Smart Plant — lab runbook
Use the repository root and follow the active ESP32 and Raspberry Pi directories.
No Monsoon run is required for this functional test. Keep the original wiring,
model and supply arrangement. No energy values are inferred from short functional runs.

## Before connecting hardware
- Fetch main and note git rev-parse HEAD on both computers. Use matching code.
- Install ESP-IDF 6.1 and open its PowerShell. Identify the ESP32 COM port.
- On Pi 4B use Raspberry Pi OS Bookworm 64-bit, Python 3.11; first setup needs
  Internet. Ensure system clock is reasonable before taking evidence.
- Power off/disconnect both boards before wiring. Check WIRING.md, common ground,
  GPIO26 -> GPIO3 pin 5, GPIO17 -> GPIO15 pin 10, GPIO16 -> GPIO14 pin 8.
  No power wire between GPIOs. Never use a 5 V UART signal.
- On Pi enable serial hardware and disable serial login via sudo raspi-config
  (Interface Options > Serial Port: login shell No, hardware Yes), reboot.
  Check ls -l /dev/serial0. Check EEPROM using sudo rpi-eeprom-config.
  If needed use sudo -E rpi-eeprom-config --edit, set WAKE_ON_GPIO=1 and
  POWER_OFF_ON_HALT=0, reboot and verify. Remove conflicting gpio-shutdown overlay.

## Prepare Pi once
From repo root on Pi:
```bash
sudo apt update
sudo apt install -y python3-venv python3-picamera2 python3-numpy python3-pil
cd raspberry_pi
chmod +x ./*.sh
sudo systemctl disable --now smartplant-optimized.service # only if already installed
./prepare_raspberry_pi.sh
./check_raspberry_pi.sh
```
Run as ordinary user with sudo privileges, not root. If camera access fails
(for example `dw9807: Device or resource busy` when PipeWire/WirePlumber holds
libcamera on Raspberry Pi OS Trixie/Bookworm), install the bundled WirePlumber
configuration and restart the user service:
```bash
mkdir -p ~/.config/wireplumber/wireplumber.conf.d
cp wireplumber/51-disable-libcamera.conf ~/.config/wireplumber/wireplumber.conf.d/
systemctl --user restart wireplumber
```
Check CSI ribbon, camera permissions and `rpicam-hello --list-cameras`.
The preflight classifies a real captured image but does not assert that an arbitrary
plant/photo is biologically healthy; known-image classifications are separately checked.

## Calibrate once, apply to every profile
The lab-measured soil calibration from the 2026-11-25 hardware validation
(`DRY_RAW=1246`, `WET_RAW=2390`, `CONFIG_SMART_PLANT_SOIL_CALIBRATED=y`) is
pre-configured in `esp32/sdkconfig.defaults` and applies to both BASELINE and
OPTIMIZED profiles. If using a different soil sensor or substrate, re-measure
and update via `menuconfig`.
Open the ESP-IDF terminal in esp32/. Replace COM4 with actual port.
```powershell
idf.py -B build-baseline -D "SDKCONFIG=sdkconfig.baseline" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.baseline.defaults" build
idf.py -B build-baseline -D "SDKCONFIG=sdkconfig.baseline" -p COM4 flash monitor
```
With calibration disabled, read repeated Soil ADC raw values in the intended dry
reference and intended wet reference (do not immerse electronics). Average several
stable values for each. Endpoints must be distinct, 0–4095, not saturated/unstable.
Save values, sensor/soil conditions and raw readings. Exit monitor (Ctrl+]).
```powershell
idf.py -B build-baseline -D "SDKCONFIG=sdkconfig.baseline" menuconfig
```
In PECD Smart Plant set dry raw, wet raw, enable confirmed calibration. Save.
Then build/flash using the same SDKCONFIG argument. Repeat these exact endpoint
settings in every other profile, including the final optimized config. Never
invent endpoints. Do not delete calibrated config files inadvertently.
The existing alarm thresholds are RH > 50%, temperature < 15 C, soil < 300/1000.
Stable test conditions require all three rules false and both sensors valid.
If necessary arrange the environment or use a clearly labelled test-only threshold
change applied to both modes; restore original thresholds for final firmware.

## BASELINE functional evidence

Build and flash BASELINE using the shared calibration and profile-specific defaults, then disable the autonomous Pi service and launch the final baseline:

```bash
sudo systemctl disable --now smartplant-optimized.service # if installed
cd raspberry_pi
./run_baseline.sh
```

Use nominal 20 s sensing and 1800 s camera cadence. Record ESP USB console and Pi CSV/events; verify capture and classification at startup and the next scheduled image. Stop with `./stop_test.sh` before changing profiles.

## OPTIMIZED functional evidence

Build and flash OPTIMIZED using the shared calibration and production 20 s sleep / 90 / 360 cycles. Install the autonomous service:

```bash
cd raspberry_pi
./install_optimized_power_service.sh
sudo reboot
```

Record host-timestamped ESP USB logs and Pi events. Confirm capture/inference followed by poweroff request and subsequent GPIO wake; keep external power supplied. Allow each Pi activity to finish before inducing a new alarm. Validate normal and stable intervals under appropriate sensor conditions. Production HALT is mandatory in the public optimized launchers. To retrieve evidence, use the boot-partition maintenance marker `smartplant-maintenance` (create it while Pi is active or on the accessible FAT boot partition with power disconnected), boot for maintenance, then remove the marker before resuming production. Do not enable the gpio-shutdown overlay.

## Archive evidence on Pi (after each test, with runner stopped)
From raspberry_pi/:
```bash
LABEL=baseline # or optimized
DEST="lab-evidence/${LABEL}-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$DEST"
for f in events_log.txt test_events.csv runtime_baseline.log runtime_optimized.log images; do
  if [ -e "$f" ]; then cp -a "$f" "$DEST/"; fi
done
git rev-parse HEAD > "$DEST/commit.txt"
journalctl -u smartplant-optimized.service --no-pager > "$DEST/service-journal.txt" || true
```
Keep the USB log from the host separately with the same label, plus a note of
actual intervals, calibration, configuration and manual boot/test actions.
Files are append-only; do not confuse older run IDs with the current test.
After confirming the archive, move old active logs/images out of the runtime
directory before the next separate experiment (do not delete historical evidence).
Poweroff logs indicate a request, not proof of physical HALT. Note observed state.

## Acceptance
Both modes compile; Pi preflight passes; real samples and camera/inference
are visible; optimized policy transitions and actual halt/wake are corroborated.
No guarantee of exact wall-clock cadence (20 s sleep plus awake overhead),
no claim of six-day reliability, no new physical power measurement.
