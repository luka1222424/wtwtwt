> **Historical analysis, superseded for current timing and projections.** This document preserves the historical Monsoon extraction and earlier assumptions. The authoritative current hardware evidence and updated model are in [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md). The historical power coefficients are conditional inputs, not new measured power.

# Independent technical and mathematical audit — Smart Plant Monitoring

**Audit date:** 25 November 2026  
**Repository / evaluated commit:** `luka1222424/wtwtwt` at `dde400a35e75941d97ead55a9936e1d60b824438`  
**Scope:** read-only review of the active implementation, original Monsoon archives and six-day model. No production files, repository history or source code were changed.

## Executive verdict

**PASS WITH CORRECTIONS.**

The active BASELINE and OPTIMIZED implementations match the stated architecture. The raw-data calculations independently reproduce the repository's principal coefficients and projections to much better than 0.01%. The central conclusion remains defensible as a **conditional six-day projection**: the dynamic optimized scenario is approximately **194.6 Wh**, compared with approximately **264.9 Wh** for the fairer final BASELINE model, an estimated saving of approximately **70.3 Wh (26.5%)**.

The projection must not be called a new electrical measurement or evidence of six-day reliability. The main remaining uncertainty is transferability from the historical schedules to the new firmware. The historical presentation must also not be used as the final evaluation because it presents the obsolete 2 s / 60 s scenario and 28.89% result.

## 1. Evidence and raw-data quality

### Integrity

| Input | SHA-256 verification | ZIP CRC verification | Result |
|---|---|---|---|
| `baseline.zip` (the supplied copy of documented `baseline(2).zip`) | `12a30d...bb825e2` matched | all entries passed | PASS |
| `optimzed.zip` (the supplied copy of documented `optimzed(4).zip`) | `4b6e63...488cf7d` matched | all entries passed | PASS |
| Seven CSV files | all hashes matched `evaluation/data/input_manifest.csv` | n/a | PASS |
| Historical PPTX supplied as `baseline-optmized-final.pptx` | `47707d...3239cfd17` matched | n/a | PASS |

The archives contain five BASELINE and two OPTIMIZED CSV/PT5/CD5 triplets. ZIP CRC protects all archive entries. This audit independently used the original CSV exports. It did not decode the proprietary PT5/CD5 containers, so it does not establish a second-format equivalence between a PT5 file and its CSV export.

### Timestamp-based raw-trace results

Power values were converted from mW to W and integrated directly using

`E = sum(0.5 * (P[i] + P[i+1]) * (t[i+1] - t[i]))`.

| Trace | Valid samples | Duration (s) | Maximum gap (ms) | Energy (J) | Mean power (W) | Status |
|---|---:|---:|---:|---:|---:|---|
| BASELINE 1 | 3,597,019 | 719.4870 | 6.6 | 1391.8011 | 1.934435 | accepted |
| BASELINE 2 | 1,208,343 | 241.6870 | 4.0 | 460.3285 | 1.904647 | accepted |
| BASELINE 3 | 1,113,442 | 222.7152 | 2.8 | 425.8125 | 1.911915 | accepted |
| BASELINE 4 | 1,146,761 | 229.3730 | 2.0 | 436.3121 | 1.902194 | accepted |
| BASELINE 5 | 1,145,230 | 229.0884 | 3.2 | 437.4408 | 1.909485 | accepted |
| OPTIMIZED 2 | 3,087,445 | 617.5722 | 3.0 | 1176.1108 | 1.904410 | accepted, primary |

All accepted traces are monotonic, non-negative and have a median interval of 0.200 ms, consistent with 5 kHz. Their short gaps were retained in timestamp integration; no large gap was interpolated.

OPTIMIZED 1 is not a whole valid experiment. A strict raw-line check found **5,008 invalid-format rows** between lines 1,394,227 and 1,440,021, plus non-monotonic/corrupted data. Two guarded clean sections are internally valid: 278.6768 s / 598.6975 J and 319.2126 s / 711.7009 J. They are corroboration only, not independent whole experiments, and were correctly excluded from primary coefficients.

## 2. Independent waveform extraction

I used a separately written analysis, rather than executing or accepting `evaluation/analyze_energy.py`.

* Samples were grouped into complete 20 ms bins.
* BASELINE camera-like events were identified as peaks above 4 W with at least 20 s separation. Six-second event windows and ordinary-operation intervals were separated.
* The recurring BASELINE sensing waveform was phase-folded near 0.5 Hz. The background reference used the lowest 60% of phase means, then the periodic increment was subtracted from ordinary mean power.
* For intact OPTIMIZED 2, the low-activity reference was the median of 20 ms bins below 1.4 W. Long Pi-like activity windows were separated from short sensor-like pulses, with quiet flanks required.

This is an inference from aggregate Main-channel power. It does not electrically isolate the ESP32, Raspberry Pi, camera, ONNX model, buzzer or individual boot phases.

### Extracted coefficients

| Coefficient | Repository | Independent audit | Absolute deviation | Interpretation |
|---|---:|---:|---:|---|
| BASELINE background | 1.835318 W | 1.835291 W | -0.000027 W | equivalent |
| BASELINE sensing increment | 0.050572 J | 0.050612 J | +0.000040 J | equivalent |
| BASELINE camera/ONNX increment | 2.701609 J | 2.697825 J | -0.003785 J | equivalent |
| OPTIMIZED low activity | 1.334776 W | 1.334776 W | +0.000000055 W | equivalent |
| OPTIMIZED sensing increment | 0.092473 J | 0.092336 J | -0.000138 J | equivalent |
| OPTIMIZED Pi-like block increment | 56.046418 J | 56.013955 J | -0.032462 J | equivalent |
| OPTIMIZED Pi-like block duration | 34.644 s | 34.620 s | -0.024 s | equivalent |
| Historical sensor period in OPTIMIZED 2 | 10.340 s | 10.340 s | 0 s | confirmed |

For BASELINE, equal weighting across the five runs gives sample SDs of 0.01940 W for background, 0.00130 J for sensing and 0.22704 J for camera-like events. These describe between-recording variation, not a confidence interval.

## 3. Implementation audit

### BASELINE

The firmware uses a 20,000 ms cycle constant and delays only the unused part of the cycle. The Pi runner starts a capture immediately, then schedules the next capture at 1,800 s. Thus the final source implements the fairer 20 s sensing / 30 min image schedule, not the historical 2 s / 60 s schedule.

### OPTIMIZED

The firmware retains policy and rule state in RTC memory, reads sensors, writes UART evidence, evaluates alarms, optionally sends an open-drain GPIO26 low pulse to Pi GPIO3, then enters a 20 s timer deep sleep. The Pi service performs one capture/inference attempt per boot, logs success or failure, flushes storage and requests orderly poweroff. The EEPROM requirement `WAKE_ON_GPIO=1` and `POWER_OFF_ON_HALT=0` is documented.

The policy implementation has the intended ordering:

1. increment `since_wake` and update consecutive stable cycles;
2. give a newly active alarm priority;
3. then give a newly detected sensor fault priority;
4. otherwise apply 90-cycle normal or 360-cycle stable scheduling;
5. reset `since_wake` only after a successful GPIO pulse.

Persistent alarm bits do not re-trigger every sample. New alarm bits do. Missing calibration blocks stable qualification but is not treated as an urgent hardware fault. A GPIO success is only a successful electrical request. It does not acknowledge a Pi boot, camera capture, inference, or halt.

## 4. Independent six-day calculations

For `T = 518400 s`, final BASELINE counts are `25920` sensing events and `288` image events. The independent calculation is:

`E_baseline = 144 * P_background + (25920 * e_sensor + 288 * e_camera) / 3600`

| BASELINE component | Independent energy (Wh) |
|---|---:|
| Background | 264.281861 |
| Sensing/logging | 0.364406 |
| Camera/ONNX | 0.215826 |
| **Total** | **264.862094** |

For OPTIMIZED, the independent cycle period is `20.34 s`, hence `ceil(518400 / 20.34) = 25,487` sensing cycles. Independent policy simulation over the half-open interval `[0, 518400)` produced the following exact request counts. It includes one separate initial manual Pi boot when calculating activity blocks.

| Scenario | Normal requests | Stable requests | New-alarm requests | GPIO requests | Activity blocks |
|---|---:|---:|---:|---:|---:|
| Stable | 1 | 70 | 0 | 71 | 72 |
| Fixed normal control | 283 | 0 | 0 | 283 | 284 |
| Dynamic synthetic scenario | 49 | 47 | 12 | 108 | 109 |

The shortest simulated GPIO-request separation is 1,830.6 s, far greater than the approximately 34.6 s historical Pi block. The scenario therefore has no predicted overlapping Pi blocks.

### Projection comparison

| Scenario | Repository result (Wh) | Independent same-model result (Wh) | Difference (Wh) |
|---|---:|---:|---:|
| BASELINE | 264.866048 | 264.862094 | -0.003955 |
| OPTIMIZED stable | 193.980180 | 193.978571 | -0.001609 |
| OPTIMIZED fixed normal | 197.271416 | 197.267915 | -0.003500 |
| OPTIMIZED dynamic | 194.554594 | 194.552655 | -0.001939 |

The dynamic independent same-model result gives `264.862094 - 194.552655 = 70.309439 Wh`, or **26.545%** saving. The tiny differences arise from independently chosen complete-bin boundaries, not a substantive mathematical disagreement.

## 5. Required correction: overlap accounting

The repository model subtracts final-period sensor overlaps from the all-sensor count:

`N_overlap = N_Pi * duration_Pi / 20.34`.

However, the measured Pi-like block includes sensing events from the historical approximately 10.34 s cycle, not the final 20.34 s cycle. If component accounting is intended to be physically additive, the more internally consistent correction is:

`E = H*P_low + N_sensor*e_sensor + N_Pi*(e_block - duration_Pi/10.34*e_sensor)`.

With the independently extracted values, this changes the dynamic scenario from **194.552655 Wh** to **194.548053 Wh**. The difference is only **0.004602 Wh** over six days, so it does not change the conclusion or rounded headline. It should nevertheless be described as a model-choice correction, rather than claiming an exact component separation.

Recommended rounded final statement: **BASELINE about 264.9 Wh; dynamic OPTIMIZED about 194.6 Wh; estimated saving about 70.3 Wh or 26.5% over six days.**

### Source references for this finding

* `docs/MATHEMATICAL_CALCULATIONS.md:303` explicitly says the measured combined Pi block contains sensing at historical cadence, then estimates overlap at the final cadence.
* `evaluation/analyze_energy.py`, function `project`, implements the same `N_overlap = N_Pi * d_Pi / tau_final` convention.
* The independent raw extraction found the historical OPTIMIZED sensor period to be 10.340 s, while the final model uses 20.340 s. The correction above changes accounting only. It does not reinterpret the measured aggregate Pi block as separate camera or ONNX energy.

## 6. Sensitivity and limitations

The following are method-dependence checks, not statistical confidence intervals.

* Varying BASELINE camera windows from 2.5 to 4.0 s and quiet phase fraction from 40% to 80% gave 264.64–265.94 Wh. Background-reference selection dominates that span.
* Varying the OPTIMIZED low-activity threshold from 1.38 to 1.42 W and block-edge extension from 0.30 to 0.42 s gave 194.5516–194.5543 Wh for the dynamic scenario.
* This narrow segmentation sensitivity does not quantify transferability to the final firmware, unknown Pi HALT electrical state, deployment failures, altered UART logging, alarms, buzzer energy, or six-day environmental variability.
* Historical OPTIMIZED 1 is corrupted, leaving one intact primary optimized trace. It cannot support a conventional experimental replication interval.
* The aggregate low-activity value is not a separate Raspberry Pi measurement. Treating it as six-day background is an explicit model assumption.
* The final firmware's 20 s sleep and adaptive 90/360 policy were not directly energy-measured. Historical traces used different schedules.
* The dynamic environmental alarm timetable is synthetic. It demonstrates policy consequences, not observed plant behaviour.
* A GPIO request has no acknowledgement handshake. Real Pi boot/capture/halt outcomes must be verified by physical logs.

## 7. Findings by severity

### Critical

None found in the mathematical arithmetic or active implementation.

### Major

1. **Do not use the historical PPTX as the final evaluation.** Slides 3–10 and 16 state 2 s sensing, 60 s camera cadence, 360-cycle-only optimization, 273.68 Wh versus 194.60 Wh and 28.89% saving. Those values belong to the old scenario and would contradict the fairer final baseline and adaptive model.
2. **The final values are projections, not measurements.** `docs/MATHEMATICAL_CALCULATIONS.md:49`, `docs/ENERGY_RESULTS.md:1–3`, and `docs/HANDOFF.md:§5` label the old and new results as historical coefficients and conditional projections. The report must retain that distinction because no end-to-end physical energy measurement of the final firmware exists.

### Minor

1. The sensor-overlap correction should reference the historical sensing period embedded in the measured Pi blocks, or the paper should present the component split as an approximate accounting convention. The total effect is only a few milliwatt-hours over six days.
2. The proprietary PT5/CD5 data was preserved and archive-CRC-checked, but not decoded independently. The audit therefore validates the original CSV exports, not cross-format equality.
3. `esp32/main/camera_policy.h:31–38` and `esp32/main/main.c:487–491` intentionally treat a successful GPIO pulse as a policy success. `raspberry_pi/smartplant_pi/experiment_runner.py:83–140` logs capture/processing/poweroff separately. This is an implementation limitation, not a bug: GPIO has no Pi acknowledgement.

## 8. Suitability for the LNCS report

The evidence is sufficient for a carefully worded six-page LNCS university report if the report:

* labels raw trace integrals as measured historical data;
* labels component coefficients as waveform-inferred aggregate-system quantities;
* labels all six-day results as conditional projections;
* uses the final fair baseline and adaptive results, not the historical PPTX values;
* discusses the no-acknowledgement GPIO path, changed historical schedules, one intact optimized trace, synthetic alarm scenario and missing physical validation;
* avoids any claim of individual Pi, camera, ONNX or sensor hardware power isolation.

Under those conditions, the conclusion that most estimated saving comes from the low-power/HALT architecture rather than adaptive scheduling alone is supported by the model. A claim that the final physical system has already achieved the projected energy reduction would not be supported.
