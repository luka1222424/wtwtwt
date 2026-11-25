# Smart Plant Monitoring

Two final operating profiles: **BASELINE** (always-on Pi and ESP32, 20 s sensing and 1800 s imaging) and **OPTIMIZED** (ESP32 deep sleep, dynamic 90/360-cycle and event-triggered Pi wake, autonomous HALT after one capture/inference). Both use the hardware-tested sensor/camera drivers and calibration (1246 dry / 2390 wet).

**144-hour conditional projection:** BASELINE 264.866 Wh; OPTIMIZED 194.547 Wh; **26.5488% saving**. Historical Monsoon power coefficients combined with observed final-profile cadence, not a new electrical measurement.

- [Current functional evidence, equations and limitations](docs/CURRENT_EVALUATION.md)
- [Reproduce current two-profile evaluation and figures](evaluation/)
- [Project handoff](docs/HANDOFF.md), [lab runbook](docs/LAB_RUNBOOK.md), [wiring](esp32/docs/WIRING.md)
- [ESP32 firmware](esp32/), [Raspberry Pi application](raspberry_pi/), [adaptive policy](docs/ADAPTIVE_SCENARIO.md)

Final-profile hardware tests: 92 BASELINE and 174 OPTIMIZED sensor records, 174 deep-sleep entries, six optimized GPIO requests, six captures, five successful inferences and five poweroff requests. All 172 consecutive optimized policy transitions agree with the implementation. The hardware-tested runtime passed 40 CI tests and both ESP-IDF builds. Stable 360-cycle operation was tested in software but not physically reached. No new power measurement or six-day reliability is claimed.

Development evidence and broader model sensitivity controls are preserved at the [previous audited revision](https://github.com/luka1222424/wtwtwt/tree/d45c1f514402bac7c8c341b9ac01e7dc46ed9542); they are not additional submitted operating profiles. Raw measurements remain available via the pinned evidence links in CURRENT_EVALUATION.md.
