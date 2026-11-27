# Current evaluation — 25 November 2026

## Implementation and provenance
Final-profile evidence: [BASELINE](https://github.com/amarkrasniqi54321-ctrl/wtwtwt/tree/54dca92055e7e58dbca2194c67b0cfc151e1ef20/meritve_2026-11-25/baseline_meritev_30min_2026-11-25) and [OPTIMIZED](https://github.com/amarkrasniqi54321-ctrl/wtwtwt/tree/54dca92055e7e58dbca2194c67b0cfc151e1ef20/meritve_2026-11-25/optimized_prod_validation_2026-11-25). Shared calibrated sensing (dry 1246/wet 2390) and camera acquisition are used in both profiles; optimized entrypoints enforce the HALT-enabled path. BASELINE: awake ESP32, nominal 20 s sensing, continuously running Pi with capture/ONNX at startup and every 1800 s. OPTIMIZED: 20 s deep sleep plus overhead, RTC policy state, GPIO wake on a newly active alarm bit or new sensor fault, otherwise after 90 cycles or after qualification 360 cycles. Qualification requires a prior successful GPIO request and 90 consecutive valid alarm-free samples. Pi boots, captures and classifies once, then requests HALT; external power remains supplied. GPIO success is not a Pi acknowledgement.

## Measured functional results
| Test | Samples | Mean consecutive interval (s) | Median (s) | Valid air | Valid soil | Deep sleep entries | Captures / successful inference |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 92 | 20.000440 | 20.000 | 92 | 92 | 0 | 2 / 2 |
| Optimized | 174 | 20.427157 | 20.375 | 174 | 140 | 174 | 6 / 5 |

266 CSV measurements across the two final profiles; 174 optimized deep-sleep entries. One sequence reset 217→2 with 55.189 s gap excluded from cadence; ordinary longer intervals remain. Production soil faults (34 invalid samples) were deliberately induced according to operator. Six GPIO requests (one scheduled, one new alarm, four faults); first preceded manual reboot and last came 21.894 s after alarm, so neither implies an extra boot. Six distinct Pi runs, six captures, five successful inferences and five poweroff requests; final run cancelled for maintenance. External SSH observations corroborate initial and alarm-triggered runs. Unsynchronised Pi clock and missing persistent earlier boot journals prevent independent exact alignment of every reported boot and measurement of HALT duration. No UART samples reached Pi in the short production windows; external host retained ESP data. All 172 consecutive optimized policy transitions (excluding first record and reset boundary) matched the C implementation; all observed intervals were 90, stable counters zero. The 360-cycle branch is not physically validated. Inference outputs are not verified biological ground truth. [Derived functional data](../evaluation/current/).

## 144-hour energy model based on physical power measurements
Use [coefficients](../evaluation/data/model_coefficients.csv) derived from physical aggregate system power measurements with the Monsoon Power Monitor. During the power measurements, baseline sensing and imaging intervals were about 2 s and 60 s; optimized timer sleep was 10 s. Five complete BASELINE recordings, one complete OPTIMIZED recording; corrupt second optimized trace contributes partial-tail sensitivity only. Power measurement analysis, original archive SHA256 and audit: [mathematical calculations](MATHEMATICAL_CALCULATIONS.md). No power trace was recorded for the final HALT-enabled profile; applying the measurement-derived coefficients to that profile is a modeling assumption.

H=144 h; T=518400 s; half-open [0,T), sample count ceil(T/period), initial activity at t=0. Baseline period 20.000439560 s, optimized 20.427156977 s. 25920 versus 25378 samples (2.09% fewer). 90/360 cycles approximately 30.641/122.563 min. Baseline 288 image events.

E_B = H P_B + (N_Bs e_Bs + N_Bc e_Bc)/3600.
E_O = H P_O + (N_Os e_Os + N_Pi e_Pi,net)/3600.
Overlap within the measured activity block: e_Pi,net = 56.0464179211 - 34.644 * 0.0924734025 / 10.34 = 55.7365873064 J. Do not substitute the final cadence for the 10.34 s sensing period in the Monsoon traces. Reference powers 1.8353180533 W and 1.334775802 W are combined-system values. Retain the 34.644 s activity block derived from the power measurements; ~9 s application start-to-poweroff request excludes boot and final shutdown, so cannot replace it.

Scenario: two synthetic two-hour alarm episodes per day (08–10 and 18–20), otherwise valid alarm-free samples; no sensor faults or failed GPIO pulses. All requests assumed complete nonoverlapping blocks, plus one initial manual boot. Do not extrapolate deliberately induced laboratory fault rates.

| Scenario | Wh | Saving vs baseline | Requests + initial |
|---|---:|---:|---:|
| BASELINE | 264.866048 | — | 288 image events |
| OPTIMIZED (adaptive) | 194.547182 | 26.548841% | 108 + 1 |

Adaptive: 49 normal, 47 stable, 12 new-alarm requests. Extraction-variant sensitivity of adaptive approximately 25.71–26.84%, not a statistical confidence interval.

## Limitations
Nominal sensing cadence comparable but not identical; threshold detection occurs on next sample, visual-only disease may wait for next image and Pi boot adds latency. No direct power measurement of the final HALT-enabled profile, no full 144 h reliability evidence, no independently quantified buzzer/retries/logging energy or UART acknowledgement. The full 40-test host/ONNX suite and both firmware builds passed CI. See [evaluation](../evaluation/) for reproduction. Raw functional logs remain on pinned fork; raw Monsoon recordings retained by the team.
