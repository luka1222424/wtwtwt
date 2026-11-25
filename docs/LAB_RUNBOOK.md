# Smart Plant — lab runbook
Use the repository root and follow the active ESP32 and Raspberry Pi directories.
No Monsoon run is required for this functional test. Keep the original wiring,
model and supply arrangement. No energy values are inferred from a short bench run.

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
Use calibrated baseline build:
```powershell
idf.py -B build-baseline -D "SDKCONFIG=sdkconfig.baseline" -p COM4 build flash monitor
```
Capture the USB serial terminal with host timestamps (e.g. serial terminal logging;
do not open two programs on COM4 simultaneously). ESP-IDF Monitor can be redirected
or logged by the chosen serial terminal. Save it as baseline-esp.log.
On Pi, in raspberry_pi/:
```bash
./check_raspberry_pi.sh --baseline
CAMERA_INTERVAL_SECONDS=60 TEST_DURATION_SECONDS=180 ./run_baseline.sh
tail -f runtime_baseline.log
```
This is a labelled accelerated camera test, not the 30 min production cadence.
Wait for RUN_MARKER, at least two distinct successful camera/ONNX records and
valid UART samples spaced ~20 s. Stop using ./stop_test.sh if still running.
Archive using the commands below before switching. For final baseline use
./run_baseline.sh without CAMERA_INTERVAL_SECONDS override.

## OPTIMIZED functional evidence
Create a separate test config; do not alter production defaults:
```powershell
idf.py -B build-bench-optimized -D "SDKCONFIG=sdkconfig.bench-optimized" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.optimized.defaults" reconfigure
idf.py -B build-bench-optimized -D "SDKCONFIG=sdkconfig.bench-optimized" menuconfig
```
Apply same soil calibration. Keep sleep 20 s; set normal cycles 6, stable cycles
18. These are ~2 min and ~6 min, not the final 30/120 min. Increase bench intervals
if the Pi cannot reliably complete boot, capture and halt within them.
```powershell
idf.py -B build-bench-optimized -D "SDKCONFIG=sdkconfig.bench-optimized" -p COM4 build flash monitor
```
Save ESP USB evidence continuously with host timestamps as optimized-esp.log.
On Pi while still running:
```bash
./check_raspberry_pi.sh --optimized
./install_optimized_power_service.sh
# Ensure no maintenance marker remains before autonomous testing:
sudo rm -f /boot/firmware/smartplant-maintenance
sudo reboot
```
Reboot starts service, captures, processes and halts; this initial manual boot is
not an ESP-triggered wake. Keep Pi power attached. Observe real halt, then:
1. Keep readings valid and alarm-free through first normal request and later
   stable request. Check CAMERA_POLICY and PI_WAKE_REQUEST on ESP USB log.
2. After Pi actually halts, create a genuine new threshold alarm (e.g. safely
   adjust soil moisture or air humidity within sensor limits). Verify the next
   sample triggers alarm_new and a real Pi boot/capture/ONNX/halt.
3. Keep condition active; check no wake every sample, and normal scheduled
   request after configured cycles. Restore healthy readings; verify stable
   interval returns. Avoid flooding the electronics or condensation.
4. Correlate Pi run IDs and camera_processing success, not just GPIO pulse status.
   A pulse during Pi boot/operation is not an acknowledgement or an extra image.
5. After the last verified orderly HALT, retrieve evidence without racing the
   service: disconnect both boards' power, then remove the Pi SD card.
   On another computer open its FAT boot partition and create an empty file
   named smartplant-maintenance (no .txt extension). Reinsert the card,
   leave ESP unpowered/disconnected from Pi signal wires, and power Pi.
   The installed service skips automatic capture/halt while that file exists.
   On Pi verify systemctl is-active smartplant-optimized.service is not active,
   then run the archive commands below. This is a maintenance boot, not a
   measurement. Never remove the card while Pi is running or writing.
   To restore autonomy, remove the marker using
   sudo rm -f /boot/firmware/smartplant-maintenance, verify the service is enabled,
   reconnect safely with both boards off, and reboot.

## Restore production configuration
Use separate final config:
```powershell
idf.py -B build-optimized -D "SDKCONFIG=sdkconfig.optimized" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.optimized.defaults" reconfigure
idf.py -B build-optimized -D "SDKCONFIG=sdkconfig.optimized" menuconfig
idf.py -B build-optimized -D "SDKCONFIG=sdkconfig.optimized" -p COM4 build flash monitor
```
In menuconfig enter same calibration; verify normal 90, stable 360 and sleep 20.
Verify baseline final 1800 s camera default. No accelerated build is evidence
of full-length interval timing.

## Archive evidence on Pi (after each test, with runner stopped)
From raspberry_pi/:
```bash
LABEL=baseline-bench # change to optimized-bench or final as applicable
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
