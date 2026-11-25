# Adaptive camera scenario

> **Current release:** see [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md) for the updated model and physical tests.

## Operational contract
- BASELINE: ESP32 awake, 20 s sensor cadence, UART logging and local alarm; Pi continuously powered, camera and ONNX at startup then every 1800 s.
- OPTIMIZED: 20 s timer deep sleep plus awake overhead; 90 cycles (~30 min) normal, 360 (~120 min) stable. First scheduled wake at 90 cycles. After 90 consecutive valid alarm-free samples and at least one wake request, extend to 360. A newly active threshold (including another rule while one is active) or new actual sensor fault requests GPIO wake on that sample. Persistent alarms return to 90 cycles, rather than rebooting each sample. Invalid or uncalibrated readings cannot qualify as stable; missing calibration alone is not an urgent hardware fault. Existing buzzer rules and cooldown unchanged.
- Pi executes one camera/ONNX attempt per boot, flushes logs, and halts after success or a logged failed attempt so future GPIO wakes can recover. Failed cycles are not successful captures. If poweroff itself fails, the service retries within a bounded restart policy. GPIO success is not a Pi acknowledgement. A pulse while Pi is already running does not guarantee an additional image. There is no Pi-to-ESP handshake or continuous Pi logging while halted. Full sensor/policy logs must be captured via ESP USB console during functional tests.
- This policy responds to ESP sensor thresholds, not visually detectable disease; the latter can go undetected between images. Current thresholds are in esp32/config/configuration.txt. Review thresholds and physically calibrate soil before stable test; no invented calibration. Sleep duration excludes active overhead; 90/360 cycles are approximate wall-clock intervals.

## Functional test (no new energy measurement)
Record ESP UART0 console with host timestamps and Pi events_log.txt. Use the production intervals (20 s sensing, 1800 s baseline imaging, 90/360 optimized cycles); maintain the GPIO and EEPROM settings in WIRING.md. Verify request status and physical boot/capture/inference/halt. A short test demonstrates functionality, not six-day reliability or energy.

## Model, not measurement
The observed production mean is 20.427157 s (90 cycles ≈ 30.641 min, 360 ≈ 122.563 min). See [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md) and [evaluation](../evaluation/) for the primary two-profile comparison, assumptions and data. Six-day adaptive projection: 194.547182 Wh vs 264.866048 Wh BASELINE. The 360-cycle branch remains physically unvalidated. No new power trace was recorded.
