# Smart Plant Monitoring

**Current release — 25 November 2026.** Integrated hardware-tested DHT11 and IMX708 camera fixes, shared soil calibration (1246 dry / 2390 wet) and WirePlumber deployment configuration from [hardware-tested source](https://github.com/amarkrasniqi54321-ctrl/wtwtwt/tree/54dca92055e7e58dbca2194c67b0cfc151e1ef20).

**144-hour conditional projection:** BASELINE 264.866 Wh; adaptive OPTIMIZED 194.547 Wh; **26.5488% saving**. Historical Monsoon coefficients combined with new observed cadence, not a new electrical measurement.

- [Current functional evidence, calculations and limitations](docs/CURRENT_EVALUATION.md)
- [Reproduce updated evaluation and figures](evaluation/)
- [Complete project handoff](docs/HANDOFF.md)
- [ESP32 firmware](esp32/) — separate BASELINE and OPTIMIZED profiles
- [Raspberry Pi application](raspberry_pi/) — optimized capture/inference once per boot, then HALT
- [Lab runbook](docs/LAB_RUNBOOK.md) and [wiring](esp32/docs/WIRING.md)
- [Adaptive specification](docs/ADAPTIVE_SCENARIO.md)
- [Historical extraction](docs/MATHEMATICAL_CALCULATIONS.md) and [independent audit](docs/INDEPENDENT_TECHNICAL_AUDIT.md)

Production evidence: 174 deep-sleep entries, six GPIO requests, six successful captures, five successful inferences and five poweroff requests. Across both optimized tests 261 observed consecutive policy transitions match the implementation. Stable 360-cycle operation remains physically unvalidated. Prior post-integration local suite reported 36 passed and 4 skipped; inspect current CI separately. No six-day reliability or new measured energy is claimed. Third-party model/image licenses and attribution remain in raspberry_pi/leaf_classifier/.
