# Smart Plant Monitoring

Luka Sveti and Amar Krasniqi — University of Ljubljana, Faculty of Computer and Information Science.

An energy-aware plant monitoring system with an ESP32-WROOM-32, Raspberry Pi 4B, DHT11, analog soil moisture sensor, IMX708 CSI camera and ONNX leaf-condition classifier.

| | BASELINE | OPTIMIZED |
|---|---|---|
| Sensing | 20 s, ESP32 awake | 20 s deep sleep plus processing time |
| Camera | Startup and every 30 min | Adaptive 90/360 cycles and new alarms or sensor faults |
| Raspberry Pi | Continuously active | One capture and inference per boot, then HALT |

Hardware tests recorded 92 baseline and 174 optimized sensor samples. Mean intervals were 20.000 s and 20.427 s. The six-day energy model combines measured final-profile timing with Monsoon-derived coefficients: **264.87 Wh vs 194.55 Wh (26.55% projected saving)**.

## Setup

- [Hardware wiring and configuration](esp32/docs/WIRING.md)
- [Installation, ESP32 builds and Raspberry Pi operation](docs/HANDOFF.md)
- [Hardware test procedure](docs/LAB_RUNBOOK.md)
- [Adaptive wake policy](docs/ADAPTIVE_SCENARIO.md)
- [Functional measurements and energy calculations](docs/CURRENT_EVALUATION.md)
- [Reproduce analysis and figures](evaluation/README.md)

The ESP32 firmware has separate baseline and optimized build profiles. On Raspberry Pi, `prepare_raspberry_pi.sh` installs dependencies and retrieves the exact, checksum-verified [ONNX model](https://huggingface.co/sarang-sketch/sarox-plangton/resolve/039a76b89e7caa1cf315b9637aaaa64bf238fbe5/model.onnx). Model and dataset [licenses and attribution](raspberry_pi/leaf_classifier/THIRD_PARTY.md) are included.

Both firmware profiles and the full host/ONNX test suite have passed CI. The 360-cycle policy has been verified in software; hardware experiments exercised normal and event-triggered operation. The 144-hour energy estimate is a model, not a continuous power recording.
