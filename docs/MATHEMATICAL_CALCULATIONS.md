> **Historical analysis, superseded for current timing and projections.** This document preserves the historical Monsoon extraction and earlier assumptions. The authoritative current hardware evidence and updated model are in [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md). The historical power coefficients are conditional inputs, not new measured power.

# Mathematical calculations — Smart Plant energy evaluation

**Status:** reproducible analysis of historical measurements + conditional projection of the final implementation. No new electrical or physical end-to-end measurements are claimed. Runtime reference: [775fa23f](https://github.com/luka1222424/wtwtwt/tree/775fa23fa16627b27625882b89710bae86d8b2cf). Analysis rerun 25 November 2026 from the original archives. Independent audit confirmed the main results and recommended historical-cadence overlap correction; the corrected model and outputs below supersede the original projection. See [independent audit](INDEPENDENT_TECHNICAL_AUDIT.md). This page is the detailed evidence base for the six-page LNCS report, not the report itself.

## 1. Original measurements and reference data

### 1.1 Primary sources and reproducibility

Only the supplied original Monsoon Main power-channel recordings and the approved historical presentation are used for energy coefficients. The final source code defines scheduling and behaviour; its energy has not yet been measured. The historical presentation is not a second independent measurement. All source files remain unchanged.

| Original input | Contents | SHA-256 |
|---|---|---|
| baseline(2).zip | 5 CSV, 5 PT5, 5 CD5 | 12a30d54347c1de296ea92618a65fb993c6a07a532dd34a9a027c35e4bb825e2 |
| optimzed(4).zip | 2 CSV, 2 PT5, 2 CD5 | 4b6e638de7bddd2bc673aaea36885974a01b289e1dc02b2c0774f4e34888cf7d |
| baseline-optmized-final(2).pptx | Historical scenario, results and measurement figures, slides 3–16 | 47707d72b985e34461decf5c48873dd5c4f52dba11e1efefe9834043239cfd17 |

The ZIPs (approximately 76 MB compressed in total) and presentation are not uploaded here; retain the original supplied copies. The individual CSV sizes and SHA-256 hashes are in [input_manifest.csv](../evaluation/data/input_manifest.csv). PT5/CD5 are retained in the original archives, not decoded in this analysis. The repository includes all extracted event records, per-run statistics, model coefficients, sensitivity outputs, simulated request timestamps and the exact analysis script. To reproduce the results and all five publication figures, obtain the two unchanged archives and follow [evaluation/README.md](../evaluation/README.md). Archive checksums permit independent source verification; a manifest does not substitute for the original raw samples.

### 1.2 Measurement boundary and trace quality

Monsoon measures the aggregate system power; the CSV column Main Avg Power is in mW, timestamps in seconds. Nominal sampling interval is 0.0002 s (5 kHz). All component labels below are incremental contributions inferred from aggregate waveform features, not isolated electrical measurements of individual devices. Neither a separate Pi-only standby power nor separately measured boot, camera, inference or buzzer energies are available.

Both ZIP CRC checks passed. Six whole recordings passed finite/non-negative power, monotonic timestamp and nominal-grid checks. Short missing-sample gaps (up to 6.6 ms in the accepted data) are integrated using the trapezoidal rule; no long corrupted gap is interpolated.

| Recording | Status | Valid samples | Duration (s) | Integrated energy (J) | Mean power (W) | Maximum native power (W) |
|---|---|---:|---:|---:|---:|---:|
| BASELINE meritev1 | Whole | 3,597,019 | 719.4870 | 1391.8011 | 1.934435 | 7.220641 |
| BASELINE meritev2 | Whole | 1,208,343 | 241.6870 | 460.3285 | 1.904647 | 7.128572 |
| BASELINE meritev3 | Whole | 1,113,442 | 222.7152 | 425.8125 | 1.911915 | 7.048322 |
| BASELINE meritev4 | Whole | 1,146,761 | 229.3730 | 436.3121 | 1.902194 | 7.166176 |
| BASELINE meritev5 | Whole | 1,145,230 | 229.0884 | 437.4408 | 1.909485 | 6.881309 |
| OPTIMIZED meritev1 | Full CSV rejected | — | — | — | — | — |
| OPTIMIZED meritev1 prefix | Partial corroboration | 1,393,226 | 278.6768 | 598.6975 | 2.148358 | 6.800980 |
| OPTIMIZED meritev1 suffix | Partial corroboration | 1,595,785 | 319.2126 | 711.7009 | 2.229552 | 7.240130 |
| OPTIMIZED meritev2 | Whole, primary | 3,087,445 | 617.5722 | 1176.1108 | 1.904410 | 7.035126 |

OPTIMIZED meritev1 has 5,008 invalid-format lines. The interval containing corruption and a 1,000-line guard on either side are excluded. Only contiguous, syntactically valid monotonic segments 0.0092–278.6860 s and 288.5274–607.7400 s are used in corroboration and method sensitivity; numerical corruption cannot be completely ruled out. Their observed Pi-like block recurrence (~62 s) differs from run 2 (~104 s), so do not combine their whole-run means as if they used identical workloads. They are two segments of one recording, not two independent experiments. Primary OPTIMIZED coefficients come only from intact run 2. There are 11,298,240 valid full-record samples and 14,287,251 analyzed samples including the two partial segments. See [trace_quality.csv](../evaluation/data/trace_quality.csv) for exact start/end times, missing samples, gaps, min/median/p95/max and integrals.

### 1.3 Historical reference scenario (presentation, not final schedules)

| Parameter | Historical BASELINE | Historical OPTIMIZED six-day model |
|---|---:|---:|
| Sensing | 2 s nominal | 20 s sleep + awake overhead |
| Camera/ONNX | 60 s nominal | Every 360 cycles |
| Pi power management | Always on | HALT between wake cycles |
| Background (Wh/144 h) | 262.86 | 192.86 |
| Sensing (Wh/144 h) | 3.79 | 0.66 |
| Camera/Pi activity (Wh/144 h) | 7.03 | 1.08 |
| Total (Wh/144 h) | 273.68 | 194.60 |
| Saving | — | 28.89% |

Original presentation projected six days from short measurements; it did not physically measure a continuous six-day run. The historical OPTIMIZED test run 2 shows approximately 10 s sleep and a Pi-like block every ~10 cycles; the 20 s/360-cycle schedule is a projection. Historical primary coefficients documented in [ENERGY_RESULTS.md](ENERGY_RESULTS.md): 1.339330 W low activity (combined system), 0.092838 J sensing, 55.848094 J Pi activity, 34.72 s block duration, 0.334625 s awake overhead (historical model). The historical 192.86 Wh background is rounded; using 192.86/144 = 1.33930556 W reproduces the rounded presentation convention. The 28.89% headline is historical, not the result of the final adaptive policy.

## 2. Common mathematical methodology

For samples at timestamps $t_i$ with recorded powers $p_i$ in mW, convert to W:

$$
P_i=p_i/1000,\qquad
E_{\mathrm{trace,J}}=\sum_{i=0}^{n-2}\frac{P_i+P_{i+1}}{2}(t_{i+1}-t_i).
$$

$$
E_{\mathrm{trace,Wh}}=E_{\mathrm{trace,J}}/3600,\qquad
\overline{P}=E_{\mathrm{trace,J}}/(t_{n-1}-t_0).
$$

The actual timestamp integral is used for the table in §1.2. For example, BASELINE run 2: 460.328527956 J / 241.687 s = 1.904647449 W. This is the **whole-trace mean at the historical workload**, not the final BASELINE background coefficient. Do not multiply that mean by 144 h after changing the schedules.

For activity identification, bin samples on the integer 5 kHz grid into 20 ms means $q_k$, nominally 100 samples per bin. Incomplete boundary bins are dropped; interior bins must be nonempty. The energy increment for activity window $A$ above the chosen reference $P_r$ is:

$$
e(A;P_r)=\Delta t\sum_{k\in A}(q_k-P_r),\qquad \Delta t=0.02\ \mathrm{s}.
$$

Signed excess is integrated rather than clipping each negative deviation; the reference must match the definition of the background. Segmentation thresholds are analytical choices, not calibrated instrument uncertainty bounds. All exact event start/end times, durations and signed energies are in [identified_events.csv](../evaluation/data/identified_events.csv).

Common six-day horizon:

$$
H=6\cdot24=144\ \mathrm{h},\qquad T=3600H=518400\ \mathrm{s}.
$$

For periodic events starting at zero within the half-open interval $[0,T)$, $N=\lceil T/\tau\rceil$. All projection energies are in Wh, background power in W, event energies in J. Full precision is retained in CSVs; displayed numbers are rounded.

## 3. BASELINE — design, implementation and energy model

### 3.1 Design: why?

A continuously running ESP32 and Raspberry Pi 4B are a reasonable, straightforward alternative to explicit power-state management. The Pi can receive and store every UART reading and perform image inference without boot latency. The final baseline uses **20 s nominal environmental sampling and 30 min image cadence** instead of historical 2 s/60 s. This avoids giving the optimized design an artificial advantage simply because the historical baseline did much more work. Both use the same sensors, calibration, threshold rules and image model. The baseline deliberately does not include timer deep sleep or Pi HALT; it isolates the architecture comparison while providing an operationally reasonable always-on solution.

### 3.2 Implementation: how?

| Design choice | Implementation in final source |
|---|---|
| Continuously active ESP32 | [main.c](../esp32/main/main.c), BASELINE mode, [sdkconfig.baseline.defaults](../esp32/sdkconfig.baseline.defaults). |
| 20 s environmental sampling | [measurement_output.h](../esp32/main/measurement_output.h): SMART_PLANT_BASELINE_INTERVAL_MS = 20000; DHT11 air temperature/RH and analog soil moisture. |
| Local threshold alerts | Monitoring and buzzer [components](../esp32/components/), [configuration.txt](../esp32/config/configuration.txt); same configured thresholds in both modes. Soil calibration must be measured, not invented. |
| Continuous UART logging | GPIO17 TX / GPIO16 RX, 115200 baud, JSON records with SMARTPLANT_JSON prefix. Pi [serial_protocol.py](../raspberry_pi/smartplant_pi/serial_protocol.py), [storage.py](../raspberry_pi/smartplant_pi/storage.py). |
| CSI capture + ONNX | [run_baseline.sh](../raspberry_pi/run_baseline.sh), [run_test.sh](../raspberry_pi/run_test.sh), [experiment_runner.py](../raspberry_pi/smartplant_pi/experiment_runner.py): startup capture then 1,800 s schedule; [camera_capture.py](../raspberry_pi/smartplant_pi/camera_capture.py), [leaf_worker_client.py](../raspberry_pi/smartplant_pi/leaf_worker_client.py). |
| Deployment | ESP-IDF 6.1 and Pi OS Bookworm 64-bit/Python 3.11; see [LAB_RUNBOOK.md](LAB_RUNBOOK.md). |

### 3.3 Extraction of historical BASELINE coefficients

For each of the five recordings independently:

1. Detect prominent camera-like peaks above 4 W in 20 ms means, with minimum separation 20 s. Exclude camera windows of ±3 s, first 20 s and final 2 s from ordinary-operation samples.
2. Estimate sensing frequency by maximizing phase coherence of positive residuals (after 51-bin median filter, clipped to 0–0.6 W) over 0.497–0.506 Hz and refine locally. This identifies recurring ~2 s historical activity, not final 20 s sampling.
3. Phase-fold ordinary power into 100 bins. Let $\mu_j$ be the mean in phase bin $j$, $\mu_{(j)}$ the sorted means and $\tau_r=1/f_r$.

$$
P_{\mathrm{quiet,phase}}=\frac1{60}\sum_{j=1}^{60}\mu_{(j)},\qquad
e_{s,r}=\tau_r\left(\frac1{100}\sum_{j=1}^{100}\mu_j-P_{\mathrm{quiet,phase}}\right).
$$

The fitted sensor-period increment includes recurring sensing/logging-related activity; non-periodic operating-system and board activity stays in the residual background. With ordinary-operation mean $\overline P_{\mathrm{ord},r}$,

$$
P_{b,r}=\overline P_{\mathrm{ord},r}-e_{s,r}/\tau_r,\qquad
e_{c,r}=\frac1{m_r}\sum_{\ell=1}^{m_r}e(A_{r,\ell};\overline P_{\mathrm{ord},r}).
$$

Camera windows use the ordinary-operation reference, which already includes average historical sensing. Thus camera energy is the increment above ordinary operation; we do not add the full camera-window energy to background. The new cadence assumes this incremental camera energy is transferable and that interactions with sensing are small; the assumption is not validated by new measurement.

| Run | Fitted period (s) | Ordinary mean (W) | Background $P_{b,r}$ (W) | Sensing $e_{s,r}$ (J) | Camera increment $e_{c,r}$ (J) | Complete events |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1.993890 | 1.887789 | 1.862895 | 0.049636 | 2.938767 | 10 |
| 2 | 1.995595 | 1.872859 | 1.848226 | 0.049159 | 2.961863 | 3 |
| 3 | 1.994326 | 1.850541 | 1.825238 | 0.050461 | 2.496551 | 3 |
| 4 | 1.994444 | 1.844433 | 1.818350 | 0.052021 | 2.540843 | 3 |
| 5 | 1.995671 | 1.847730 | 1.821882 | 0.051584 | 2.570022 | 3 |

Use equal weight per run, rather than allowing the longer first run or its larger event count to dominate. For each coefficient $x$, $\bar x=\sum_{r=1}^5x_r/5$. Exact coefficients: [baseline_coefficients.csv](../evaluation/data/baseline_coefficients.csv).

$$
P_B=1.835318053296\ \mathrm{W},\qquad
e_{B,s}=0.050572208485\ \mathrm{J},\qquad
e_{B,c}=2.701609132329\ \mathrm{J}.
$$

The 22 camera-like increments range from about 1.77 to 4.27 J. Background varies between runs (sample SD 0.01935 W); run 1 is higher, and late elevated activity lacks a clear peak at the expected phase. Retain the data and discuss uncertainty; do not assign a proven cause. Capture timing, operating-system activity and other workload differences are possible explanations, not independently established. Peaks are not removed just because they are large.

### 3.4 Final BASELINE six-day projection

$$
N_{B,s}=\frac{518400}{20}=25920,\qquad
N_{B,c}=\frac{518400}{1800}=288.
$$

Counts include an assumed first sensing and capture event at startup, no additional separate startup cost, no missed or delayed captures. Nominal cadence, not a recorded count. Raspberry Pi remains on throughout.

$$
E_B=H P_B+\frac{N_{B,s}e_{B,s}+N_{B,c}e_{B,c}}{3600}.
$$

| Component | Substitution | Wh |
|---|---|---:|
| Background | 144 × 1.835318053296 | 264.285800 |
| Sensing/logging | 25920 × 0.050572208485 / 3600 | 0.364120 |
| Camera/ONNX | 288 × 2.701609132329 / 3600 | 0.216129 |
| **Total** | Sum | **264.866048** |

$$
\boxed{E_B=264.866048\ \mathrm{Wh}},\quad
E_{B,\mathrm{day}}=44.144341\ \mathrm{Wh},\quad
\overline{P}_B=1.83934756\ \mathrm{W}.
$$

Historical coefficient cross-check (not primary): $P_{B,h}=262.86/144$, $e_{B,s,h}=3.79(3600)/259200$, $e_{B,c,h}=7.03(3600)/8640$. Hence

$$
E_{B,h}=262.86+3.79/10+7.03/30=263.473333\ \mathrm{Wh}.
$$

## 4. OPTIMIZED — design, implementation and energy model

### 4.1 Design: why?

Environmental sensing and image inference have different energy/latency requirements. The ESP32 can monitor inexpensive sensors and provide a local buzzer alarm without keeping the Pi operating. Use ESP32 timer deep sleep between readings and turn the Pi off through orderly operating-system halt after each image/inference attempt. Leave the Pi supply connected; the measured low-activity state still consumes energy. Preserve the approximately 20 s environmental cadence to meet the fairness requirement. Instead of merely fixing the camera interval to 120 min, use adaptive scheduling: a 30 min normal interval, 120 min when conditions are persistently stable, immediate wake request for a newly active environmental alarm or actual sensor fault. Persistent alarm retains regular 30 min checks rather than repeatedly waking every sample. This is intended for indoor plant monitoring with slowly changing environmental conditions, not a system requiring continuous camera coverage.

No change to the power supply, EEPROM wake architecture, sensor types, classifier or external switching hardware is proposed. Deeper PMIC power-off is outside scope; would require a revised safe wake interface and new measurements.

### 4.2 Implementation: how?

| Design choice | Implementation in final source |
|---|---|
| 20 s timer sleep | [sdkconfig.optimized.defaults](../esp32/sdkconfig.optimized.defaults), [main.c](../esp32/main/main.c): wake, read, evaluate rules, emit measurement/policy logs, request Pi if needed, enter deep sleep. Active overhead adds to the configured sleep duration. |
| Persistent state | camera policy and monitoring state in ESP32 RTC memory across deep sleep. |
| Adaptive policy | [camera_policy.h](../esp32/main/camera_policy.h): normal=90, stable=360, count consecutive valid no-alarm samples and cycles since last successful GPIO request. |
| Local threshold rules | [configuration.txt](../esp32/config/configuration.txt): temperature below 15 °C, RH above 50%, normalized soil below 300/1000. Review suitability for intended plant and calibrate soil; uncalibrated soil blocks stable state, but missing calibration alone is not a new actual sensor fault. |
| Wake mechanism | [raspberry_pi_wake.c](../esp32/main/raspberry_pi_wake.c): GPIO26 open drain, 250 ms LOW to Pi GPIO3 (physical pin 5), common ground, 3.3 V logic. EEPROM WAKE_ON_GPIO=1, POWER_OFF_ON_HALT=0; no gpio-shutdown overlay. See [WIRING.md](../esp32/docs/WIRING.md). |
| Pi processing and shutdown | [smartplant-optimized.service](../raspberry_pi/systemd/smartplant-optimized.service) starts one camera/ONNX attempt per boot; [experiment_runner.py](../raspberry_pi/smartplant_pi/experiment_runner.py) logs outcome, flushes storage and requests systemctl poweroff after completion or logged failure. A failed capture is not a successful inference. |
| Evidence and tests | ESP USB console mirrors measurements, CAMERA_POLICY and PI_WAKE_REQUEST. Pi stores events and images while running; it cannot continuously receive UART while halted. [test_camera_policy.py](../raspberry_pi/tests/test_camera_policy.py) compiles exact C policy and tests transitions. Prior runtime validation: both ESP-IDF builds and 40 automated tests passed. Current hardware end-to-end validation remains pending. |

A successful GPIO pulse does not acknowledge Pi boot, capture or shutdown. No Pi-to-ESP handshake exists. If a pulse arrives while Pi is active or shutting down, a further capture is not guaranteed. Complete six-day sensor history requires external ESP logging (Pi storage alone is incomplete). The model assumes the requests in its spaced scenarios produce equivalent Pi activity blocks.

### 4.3 Extraction of historical OPTIMIZED coefficients

Use intact OPTIMIZED meritev2 as primary. Low-activity reference:

$$
P_O=\operatorname{median}\{q_k:q_k<1.4\ \mathrm{W}\}.
$$

Long Pi-like blocks: 20 ms bins above 1.6 W, bridge short interruptions with a 26-bin binary closing; require length >3 s and quiet flanks. Exclude truncated edge blocks and extend accepted intervals by 0.36 s per side. Short sensing-like pulses outside these blocks: threshold 1.42 W, four-bin closing, length 0.20–0.90 s, guard 0.08 s on each side and separation from Pi windows. Use signed excess above $P_O$ for both:

$$
e_{O,s}=\frac1{35}\sum_{i=1}^{35}e(S_i;P_O),\qquad
e_{O,p}=\frac1{5}\sum_{j=1}^{5}e(B_j;P_O),\qquad
d_p=\frac1{5}\sum_{j=1}^{5}|B_j|.
$$

| Source | Low activity (W) | Sensor mean (J) | Sensor SD (J) | Sensor events | Pi block mean (J) | Pi SD (J) | Duration (s) | Blocks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Run 1 prefix (sensitivity only) | 1.343048 | 0.092956 | 0.002391 | 11 | 55.793865 | 0.452199 | 34.635 | 4 |
| Run 1 suffix (sensitivity only) | 1.348910 | 0.093790 | 0.001820 | 10 | 55.978194 | 0.204573 | 34.564 | 5 |
| Run 2 (primary) | 1.334776 | 0.092473 | 0.002729 | 35 | 56.046418 | 0.425529 | 34.644 | 5 |

Sample SD $s=\sqrt{\sum_i(x_i-\bar x)^2/(n-1)}$, describes within-record event variation, not uncertainty across independent hardware sessions. [optimized_coefficients.csv](../evaluation/data/optimized_coefficients.csv).

Five primary Pi blocks:

| Start (s) | End (s) | Duration (s) | Increment (J) |
|---:|---:|---:|---:|
| 73.04 | 107.52 | 34.48 | 55.520834 |
| 176.60 | 211.34 | 34.74 | 56.013449 |
| 280.18 | 314.86 | 34.68 | 56.140496 |
| 384.22 | 418.70 | 34.48 | 55.872297 |
| 487.80 | 522.64 | 34.84 | 56.685014 |

The block includes Pi boot, camera, inference, shutdown and simultaneous sensing; no independent sub-component timing/energy attribution is available. Peaks above 6 W in binned data and above 7 W in native samples are retained; exact source of spikes cannot be proven without synchronized activity logs.

Estimate historical sensing period from median consecutive identified sensor-event gaps between 9 and 12 s:

$$
\tau_{\mathrm{hist}}=10.34\ \mathrm{s},\qquad
\delta=\tau_{\mathrm{hist}}-10=0.34\ \mathrm{s}.
$$

Therefore final assumed cycle period:

$$
\tau_O=20+\delta=20.34\ \mathrm{s},\quad
N_{O,s}=\left\lceil518400/20.34\right\rceil=25487.
$$

Primary coefficient set:

$$
P_O=1.334775802\ \mathrm{W},\quad e_{O,s}=0.092473402478\ \mathrm{J},\quad
e_{O,p}=56.046417921053\ \mathrm{J},\quad d_p=34.644\ \mathrm{s}.
$$

The low-activity value is system power, **not Pi-only power**. Transferring these coefficients assumes unchanged sleep/halt architecture and approximately equivalent per-event workloads. Extra USB logging, software changes and changed sensor timing could alter power and overhead. The optimized sensor increment exceeds the baseline one because the references and active work differ; this does not imply an isolated sensor consumes more.

### 4.4 Mathematical model of the adaptive wake algorithm

Define sample index $i=0,\ldots,N_{O,s}-1$, $t_i=i\tau_O$. Inputs: bitmask $a_i$ of currently active alarm rules, valid flag $v_i$, actual fault flag $f_i$. RTC state: $c$ cycles since the last successful GPIO request, $s$ consecutive valid alarm-free samples (capped at 360), previous alarm and fault states, and $h$ indicating at least one successful wake request. Initially $c=s=0,\ a_{-1}=0,\ f_{-1}=0,\ h=0$. At every sample, before deciding:

$$
c_i^-=c_{i-1}+1,\qquad
s_i=\begin{cases}\min(360,s_{i-1}+1)&v_i=1\ \land\ a_i=0\\0&\text{otherwise}.\end{cases}
$$

$$
L_i=\begin{cases}360 & h_{i-1}=1\ \land\ s_i\ge90\\90&\text{otherwise}.\end{cases}
$$

With bitwise AND and NOT matching C, a new threshold is $a_i\ \&\ \neg a_{i-1}\ne0$, and a new fault is $f_i\land\neg f_{i-1}$. Request priority:

$$
r_i=\begin{cases}
\mathrm{alarm\_new} & (a_i\ \&\ \neg a_{i-1})\ne0\\
\mathrm{sensor\_fault} & f_i\land\neg f_{i-1}\\
\mathrm{scheduled\_120m} & c_i^-\ge L_i,\ L_i=360\\
\mathrm{scheduled\_30m} & c_i^-\ge L_i,\ L_i=90\\
\mathrm{none} & \text{otherwise}.
\end{cases}
$$

If no request: $c_i=c_i^-$, $h_i=h_{i-1}$. If request succeeds: $c_i=0,\ h_i=1$; if GPIO request fails, firmware sets $c_i=90,\ s_i=0$ to retry at a subsequent sample, without setting $h$ on failure. Store current alarm/fault as previous state. The simulation in [analyze_energy.py](../evaluation/analyze_energy.py) uses fault-free inputs and assumes successful requests; thus it models the applicable subset of the exact C logic, not faults or failed wakes. Counts are obtained by executing this recurrence on every sample, not averaging 30 and 120 min intervals.

At the modeled effective cadence, 90 cycles are 1830.6 s (30.51 min) and 360 cycles are 7322.4 s (122.04 min); first sample at t=0 means first scheduled request at cycle 90, t=89×20.34=1810.26 s. These are model timings, not measured final firmware latency.

## 5. Evaluation — reasonable alternatives, assumed scenario and results

### 5.1 Assumed operational environment

Six days of indoor monitoring of one plant. Use the same sensor thresholds and calibration for both architectures. The conditional central scenario assumes valid measurements, no actual sensor fault, no failed GPIO requests, and two persistent two-hour alarm episodes each day (08:00–10:00 and 18:00–20:00), with the same one alarm bit active in each episode. The other 20 hours per day are alarm-free. This means 12 new alarm episodes over six days. It is **synthetic, not observed environmental data, not a forecast of a particular plant**, and need not represent typical indoor conditions. For example, the configured RH threshold of 50% may keep a real system in the normal regime. Simulate every sample against these intervals.

Two controls separate effects: (i) alarm-free stable adaptive operation, and (ii) a fixed 90-cycle optimized control, equivalent to disabling extension and with no extra alarm edges. In the script the latter is implemented via the no-stability input to the policy; it is an abstract fixed-schedule comparison, not a separately measured firmware or a claim that the real sensors are invalid. The always-on final BASELINE provides the main comparison.

| Scenario | Scheduled 90 | Scheduled 360 | New alarms | Total GPIO requests | Initial Pi boot | Equivalent Pi activity blocks |
|---|---:|---:|---:|---:|---:|---:|
| Stable | 1 | 70 | 0 | 71 | 1 | 72 |
| Fixed 90-cycle control | 283 | 0 | 0 | 283 | 1 | 284 |
| Dynamic | 49 | 47 | 12 | 108 | 1 | 109 |

For stable, $\lfloor (25487-90)/360\rfloor+1=71$ requests. For fixed schedule, $\lfloor25487/90\rfloor=283$. Dynamic count is simulated; use the individual [dynamic request timestamps](../evaluation/data/wake_requests_dynamic.csv), [stable](../evaluation/data/wake_requests_stable.csv) and [normal](../evaluation/data/wake_requests_normal.csv). Each optimized scenario includes one additional initial manual Pi boot at t=0 and assumes that this has the same incremental energy/duration as a measured Pi block. That boot is not a GPIO request. No extra energy for individual buzzer alarms or startup-specific transients is quantified. Equivalent Pi blocks are assumed not to overlap or cross the simulation endpoint appreciably.

### 5.2 OPTIMIZED energy projection (audit-corrected)

The measured combined Pi block embeds sensing at the historical cadence, not at the final cadence. The independent audit recommends removing that historical expected contribution from the block coefficient, then adding all final sensing events. Let $\tau_{\mathrm{hist}}=10+\delta=10.34$ s for the primary coefficient set.

$$
e_{O,p}^{\mathrm{net}}=e_{O,p}-\frac{d_p}{\tau_{\mathrm{hist}}}e_{O,s}.
$$

The net Pi increment is still an inferred aggregate-system quantity; the fractional historical overlap is an expected-count approximation, not exact electrical isolation. Assumes the standalone sensing increment transfers to the historical Pi block and final schedule.

$$
E_O=H P_O+\frac{N_{O,s}e_{O,s}+N_pe_{O,p}^{\mathrm{net}}}{3600}.
$$

Dynamic substitution:

$$
e_{O,p}^{\mathrm{net}}=56.046417921053-\frac{34.644}{10.34}(0.092473402478)=55.736587306\ \mathrm{J}.
$$

$$
E_{O,\mathrm{dyn}}=144(1.334775802)+\frac{25487(0.092473402478)+109(55.736587306)}{3600}.
$$

$$
E_{O,\mathrm{dyn}}=192.207715488+0.654686002+1.687580005
=\boxed{194.549981495\ \mathrm{Wh}}.
$$

The original projection (194.554593581 Wh) used final-period rather than historical-period overlap; correction is -0.004612086 Wh. Independent audit coefficients give 194.548053 Wh after correction (not substituted for the primary coefficients). Mean projected power 1.3510415 W; daily energy 32.424997 Wh. Report totals to two decimals (194.55 Wh); do not double-round to 194.6 Wh from 194.55 Wh.

### 5.3 Comparison

$$
\Delta E=E_B-E_O,\qquad S=100\left(1-\frac{E_O}{E_B}\right)\%.
$$

| Model | Samples | Images or equivalent blocks | Background (Wh) | Sensing (Wh) | Camera/net Pi increment (Wh) | Total Wh/144h | Saving Wh | Saving % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BASELINE | 25920 | 288 images | 264.285800 | 0.364120 | 0.216129 | 264.866048 | — | — |
| OPTIMIZED stable | 25487 | 72 blocks | 192.207715 | 0.654686 | 1.114732 | 193.977133 | 70.888915 | 26.7641 |
| OPTIMIZED fixed 90 | 25487 | 284 blocks | 192.207715 | 0.654686 | 4.396997 | 197.259399 | 67.606649 | 25.5248 |
| OPTIMIZED dynamic | 25487 | 109 blocks | 192.207715 | 0.654686 | 1.687580 | 194.549981 | 70.316067 | 26.5478 |

All values in [projections.csv](../evaluation/data/projections.csv) retain numerical precision. **Central projected result: 26.55% reduction against the revised BASELINE**, conditional on the synthetic scenario. Approximately 98.8% of dynamic energy is background; most savings arise from sleep/HALT rather than scheduling alone.

$$
\frac{284-109}{284}\cdot100=61.62\%\ \text{fewer equivalent Pi blocks}.
$$

$$
197.259399-194.549981=2.709417\ \mathrm{Wh},\qquad
100\frac{2.709417}{197.259399}\approx1.37\%.
$$

This is the additional saving relative to fixed 90-cycle optimized control, not the entire baseline-relative saving.

### 5.4 Sensitivity and historical cross-check

Holding coefficients and sample count fixed, vary equivalent blocks $n$ from 0 to 600.

$$
\frac{dE_O}{dn}=\frac{e_{O,p}-d_pe_{O,s}/\tau_{\mathrm{hist}}}{3600}\approx0.0154824\ \mathrm{Wh}.
$$

See [activation_sensitivity.csv](../evaluation/data/activation_sensitivity.csv). This is conditional count sensitivity, not an alarm-frequency distribution or a guarantee for overlapping requests. Extra alarm and failed/retried block energies may differ.

Alternate BASELINE camera half-windows (2.5, 3, 4 s) and quiet-phase fractions (40, 60, 80%); use each OPTIMIZED source (intact and the two partial segments) for a method sensitivity envelope. Partial segments are not independent runs.

| Scenario | Main result | Method sensitivity envelope | Historical-reference model, identical scenario |
|---|---:|---:|---:|
| stable | 26.76% | 25.93–27.06% | 26.13% |
| Fixed 90 | 25.52% | 24.69–25.82% | 24.89% |
| dynamic | 26.55% | 25.71–26.84% | 25.91% |

Historical-reference model with corrected overlap: BASELINE 263.473333 Wh; stable 194.628172 Wh; fixed 90 197.898637 Wh; dynamic 195.198960 Wh. It uses previous rounded coefficients and historical 0.334625 s overhead, with the same half-open counting convention (25,494 samples). This is a reference cross-check, not an independent statistical replication. See [baseline_method_sensitivity.csv](../evaluation/data/baseline_method_sensitivity.csv), [method_sensitivity.csv](../evaluation/data/method_sensitivity.csv), [model_coefficients.csv](../evaluation/data/model_coefficients.csv). The envelope is **not a confidence interval** or a complete uncertainty budget.

### 5.5 Fairness, service quality and limitations

Environmental detection: both final systems nominally sense every 20 s, but timer sleep plus estimated overhead gives optimized 20.34 s, i.e. 433 fewer readings over 144 h (1.67%). Assuming periodic operation and valid sensing, a new environmental threshold is detected by the next sample (about 20.34 s worst-case sampling delay, before processing and actual Pi boot); the baseline's nominal delay is 20 s. This is approximate, not a hard realtime guarantee. Buzzer remains local in both. In the dynamic system a new alarm can request an image earlier than baseline's next scheduled capture, but a wake request is not proof of successful image processing. Stable camera period is longer (~122 min instead of nominal 30 min); a visual-only disease need not change environmental sensors, and may be detected considerably later. Pi storage does not preserve all optimized readings while halted; external console logging is required for full history. These are quality-of-service trade-offs, not identical services.

The original recordings are short and use different event frequencies from final firmware. Per-event energy, background and active duration transfer are modeling assumptions; the current code's physical consumption, timing, calibration, successful capture rate and reliability remain unverified. One intact optimized run limits between-session uncertainty. No incremental buzzer/fault/retry cost or possible new logging overhead is modeled. Exact attribution of peaks and individual device power is unavailable without synchronized logs/isolated channels. No direct six-day measurement, no new runtime proof and no claimed statistical confidence interval. For stronger evidence, perform a few real functional cycles as described in [LAB_RUNBOOK.md](LAB_RUNBOOK.md) and record timestamped ESP and Pi logs; further power measurements would be needed to validate these energy projections directly.

### 5.6 Figures and interpretation

The [reproduction script](../evaluation/analyze_energy.py) generates five labelled PNG (300 dpi) and SVG figures: fig1_baseline_trace (historical run 2; periodic peaks); fig2_optimized_trace (historical run 2; low-activity floor, sensor spikes, Pi block); fig3_projected_energy (energy breakdown, background dominates); fig4_cumulative (conditional cumulative model, not a six-day trace; baseline uses a linearized total and optimized adds simulated blocks); fig5_sensitivity (saving as a function of block count). Readable figure axes use seconds or hours, W or Wh or %. Plot large peaks without deleting them; their individual source is not established. At the six-page limit prioritize the two measured waveform panels and the projected comparison, including limitations in their captions. See the [evaluation folder](../evaluation/) for the calculation inputs and outputs.

## 6. Report preparation and evidence status

Use the [Springer LNCS proceedings guidelines](https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines), maximum six pages, a single PDF, repository URL, labelled readable figures, discussion of trends and outliers. Design and implementation sections above answer why/how; evaluation answers comparison and assumed operating scenario. Cite the supplied measurement provenance and the third-party model/dataset using [ASSETS.json](../raspberry_pi/leaf_classifier/ASSETS.json) and licenses; verify the exact external reference details before submission. The two author names appear on the historical slides; their individual contribution statement is **not established by these measurements** and must be confirmed by the authors before submission. Do not invent contributions, physical logs or instructor approval. The draft is due for optional feedback 25 November and final report 27 November 2026.

**Bottom line:** the final adaptive design is implemented and the conditional energy calculation is reproducible. On the stated six-day scenario it projects 194.55 Wh vs 264.87 Wh. The evaluation demonstrates a credible modeled trade-off; it does not assert that the changed firmware has physically achieved these numbers.
