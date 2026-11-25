# Power characterization and energy calculations

The Monsoon Power Monitor measured aggregate system power, not separate device rails. Five complete BASELINE traces and one complete OPTIMIZED trace provide the primary coefficients. The other optimized recording contains 5008 malformed rows; only two contiguous valid segments contribute to sensitivity analysis. Raw archives are retained by the authors.

| Original archive | SHA-256 |
|---|---|
| baseline(2).zip | 12a30d54347c1de296ea92618a65fb993c6a07a532dd34a9a027c35e4bb825e2 |
| optimzed(4).zip | 4b6e638de7bddd2bc673aaea36885974a01b289e1dc02b2c0774f4e34888cf7d |

Individual CSV hashes: [input manifest](../evaluation/data/input_manifest.csv). Nominal 5 kHz sampling; convert mW to W and integrate using recorded time differences, by the trapezoidal rule. No interpolation across the corrupted segment. Trace statistics: [trace quality](../evaluation/data/trace_quality.csv).

Waveform segmentation uses 20 ms means, phase-folded sensing activity, local camera-like excess energy and Pi-like activity blocks. The baseline parameters are equal-weight means across five runs; the optimized primary parameters come from the complete optimized trace. Event energies are calculated above reference background power. The extracted parameters and [event inventory](../evaluation/data/identified_events.csv) are retained with [per-run baseline](../evaluation/data/baseline_coefficients.csv) and [optimized](../evaluation/data/optimized_coefficients.csv) estimates. Exact extraction and segmentation settings are in [analyze_energy.py](../evaluation/analyze_energy.py).

| Parameter | Baseline | Optimized |
|---|---:|---:|
| Background W | 1.8353180533 | 1.3347758020 |
| Sensor increment J | 0.0505722085 | 0.0924734025 |
| Camera / Pi block increment J | 2.7016091323 | 56.0464179211 |

The historical Pi activity block includes sensing at its characterization cadence (10.34 s). Subtract its estimated overlap: 34.644 / 10.34 × 0.0924734025 = 0.309830615 J. Net Pi block energy is 55.736587306 J.

Use these characterized power coefficients with the observed timing of the final two profiles (20.000440 s and 20.427157 s). For H = 144 h and T = 518400 s, the baseline has 25920 samples and 288 camera events; the adaptive workload has 25378 samples and 109 assumed complete Pi blocks, including initial boot. Energy in Wh:

- BASELINE: H × P_B + (N_Bs × e_Bs + N_Bc × e_Bc)/3600 = 264.866048.
- OPTIMIZED: H × P_O + (N_Os × e_Os + N_Pi × e_Pi,net)/3600 = 194.547182.
- Relative reduction: 100 × (1 − E_O/E_B) = 26.548841%.

Transfer of the characterized coefficients and completion of nonoverlapping requested activities are model assumptions. The sensitivity range over extraction variants is approximately 25.71–26.84%, not a statistical confidence interval. The final operating scenario, measured functional evidence and limitations are in [CURRENT_EVALUATION.md](CURRENT_EVALUATION.md). The final-profile power was not recorded continuously for 144 hours.
