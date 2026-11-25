# Current evaluation — 25 November 2026

## Implementation and provenance
Hardware-tested source: [54dca92055e7e58dbca2194c67b0cfc151e1ef20](https://github.com/amarkrasniqi54321-ctrl/wtwtwt/tree/54dca92055e7e58dbca2194c67b0cfc151e1ef20). Original evidence: [three test folders](https://github.com/amarkrasniqi54321-ctrl/wtwtwt/tree/54dca92055e7e58dbca2194c67b0cfc151e1ef20/meritve_2026-11-25). Active DHT11 and camera fixes, calibration defaults (dry 1246/wet 2390) and deployment instructions integrated verbatim. BASELINE: awake ESP32, nominal 20 s sensing, continuously running Pi with capture/ONNX at startup and every 1800 s. OPTIMIZED: 20 s deep sleep plus overhead, RTC policy state, GPIO wake on a newly active alarm bit or new sensor fault, otherwise after 90 cycles or after qualification 360 cycles. Qualification requires a prior successful GPIO request and 90 consecutive valid alarm-free samples. Pi boots, captures and classifies once, then requests HALT; external power remains supplied. GPIO success is not a Pi acknowledgement.

## Measured functional results
| Test | Samples | Mean consecutive interval (s) | Median (s) | Valid air | Valid soil | Deep sleep entries | Captures / successful inference |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 92 | 20.000440 | 20.000 | 92 | 92 | 0 | 2 / 2 |
| Optimized bench | 89 | 20.406693 | 20.374 | 89 | 89 | 90 | 1 / 1 |
| Optimized production | 174 | 20.427157 | 20.375 | 174 | 140 | 174 | 6 / 5 |

355 CSV measurements; 264 logged deep-sleep entries (bench and production). Log and CSV windows differ slightly. One sequence reset 217→2 with 55.189 s gap excluded from cadence; ordinary longer intervals remain. Production soil faults (34 invalid samples) were deliberately induced according to operator. Six GPIO requests (one scheduled, one new alarm, four faults); first preceded manual reboot and last came 21.894 s after alarm, so neither implies an extra boot. Six distinct Pi runs, six captures, five successful inferences and five poweroff requests; final run cancelled for maintenance. External SSH observations corroborate initial and alarm-triggered runs. Unsynchronised Pi clock and missing persistent earlier boot journals prevent independent exact alignment of every reported boot and measurement of HALT duration. No UART samples reached Pi in the short production windows; external host retained ESP data. All observed 261 consecutive policy transitions (89 bench, 172 production; exclude first records/reset boundary) matched the C implementation; all intervals were 90, stable counters zero. The 360-cycle branch is not physically validated. Bench Pi was deliberately kept on. Inference outputs are not verified biological ground truth. [Derived functional data](../evaluation/current/).

## Updated 144-hour model — not new measured energy
Use historical aggregate Monsoon [coefficients](../evaluation/data/model_coefficients.csv). Five complete BASELINE recordings, one complete OPTIMIZED recording; corrupt second optimized trace contributes partial-tail sensitivity only. Historical extraction, original archive SHA256 and audit: [mathematical calculations](MATHEMATICAL_CALCULATIONS.md), [audit](INDEPENDENT_TECHNICAL_AUDIT.md). No new power profile recorded; transfer of historical waveform-inferred coefficients to current hardware is an assumption.

H=144 h; T=518400 s; half-open [0,T), sample count ceil(T/period), initial activity at t=0. Baseline period 20.000439560 s, optimized 20.427156977 s. 25920 versus 25378 samples (2.09% fewer). 90/360 cycles approximately 30.641/122.563 min. Baseline 288 image events.

E_B = H P_B + (N_Bs e_Bs + N_Bc e_Bc)/3600.
E_O = H P_O + (N_Os e_Os + N_Pi e_Pi,net)/3600.
Historical overlap: e_Pi,net = 56.0464179211 - 34.644 * 0.0924734025 / 10.34 = 55.7365873064 J. Do not substitute new cadence for historical 10.34 s. Reference powers 1.8353180533 W and 1.334775802 W are combined-system values. Retain historical 34.644 s activity block; ~9 s application start-to-poweroff request excludes boot and final shutdown, so cannot replace it.

Scenario: two synthetic two-hour alarm episodes per day (08–10 and 18–20), otherwise valid alarm-free samples; no sensor faults or failed GPIO pulses. Stable: valid alarm-free; fixed90: constant 90 without alarm edges; fixed90_alarm: same alarm edges as adaptive but never extends. All requests assumed complete nonoverlapping blocks, plus one initial manual boot. Do not extrapolate deliberately induced laboratory fault rates.

| Scenario | Wh | Saving vs baseline | Requests + initial |
|---|---:|---:|---:|
| BASELINE | 264.866048 | — | 288 image events |
| stable | 193.974333 | 26.765120% | 71 + 1 |
| fixed90 | 197.225634 | 25.537593% | 281 + 1 |
| fixed90_alarm | 197.318529 | 25.502521% | 287 + 1 |
| adaptive | 194.547182 | 26.548841% | 108 + 1 |

Adaptive: 49 normal, 47 stable, 12 new-alarm requests. Versus fixed90_alarm: 109 vs 288 blocks, 62.15% fewer; 2.771347 Wh / 1.4045% additional energy reduction. Historical extraction-variant sensitivity of adaptive approximately 25.71–26.84%, not a statistical confidence interval. Earlier audited result 194.549981 Wh under old 20.34 s timing; new result differs by -0.002800 Wh.

## Limitations
Nominal sensing cadence comparable but not identical; threshold detection occurs on next sample, visual-only disease may wait for next image and Pi boot adds latency. No direct new energy measurement, no full 144 h reliability evidence, no independently quantified buzzer/retries/logging energy or UART acknowledgement. Post-integration local tests reported 36 passed / 4 skipped (missing C compiler and ONNX dependencies); inspect current CI separately. See [evaluation](../evaluation/) for reproduction. Raw functional logs remain on pinned fork; historical raw Monsoon recordings retained by team.
