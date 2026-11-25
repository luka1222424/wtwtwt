# Energy evaluation

**Current:** [functional validation and updated mathematical model](../docs/CURRENT_EVALUATION.md). Run from the repository root:

```sh
python -m pip install -r evaluation/requirements.txt
python evaluation/analyze_current.py
```

Derived data in current/ were extracted from pinned source logs linked above. The script checks the published projection tables and generates current CSVs and seven figures (PNG/SVG) in current/generated/. Existing data/ and analyze_energy.py preserve historical Monsoon extraction and earlier audited projections (20.34 s assumption), not current results. Do not confuse measured functional evidence with projected energy.

## Historical reproduction (preserved)
# Reproducible energy evaluation

Read the historical [Mathematical calculations](../docs/MATHEMATICAL_CALCULATIONS.md).

## Reproduce

Place unchanged original baseline(2).zip and optimzed(4).zip beside this directory or pass their paths. The originals are retained by the project team; raw ZIPs are not part of this repository. Validate SHA-256 against the main calculation page and individual CSVs against data/input_manifest.csv. No fake or reconstructed raw data is included.

Install the versions used in the rerun (Python 3, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, Matplotlib 3.10.8), then run:

    python -m pip install -r requirements.txt
    python analyze_energy.py "baseline(2).zip" "optimzed(4).zip" --out results

The script validates ZIP CRCs, reads the CSVs directly, checks timestamps and data quality, extracts coefficients, simulates the policy and writes 13 CSVs plus five PNG/SVG figures. The original analysis was independently audited on 25 November 2026; the corrected script was rerun on the original ZIPs. The three projection-dependent tables use historical-cadence overlap correction; values reproduced from the same coefficients may differ in last floating-point digits. See [audit](../docs/INDEPENDENT_TECHNICAL_AUDIT.md). Floating-point last digits and SVG metadata can differ with library versions. The figures are regenerated rather than stored as full-resolution image files here.

| Output in data/ | Meaning |
|---|---|
| input_manifest.csv | Individual input CSV sizes and SHA-256 |
| trace_quality.csv | All measurement statistics and rejection/partial status |
| baseline_coefficients.csv | Per-run historical BASELINE coefficients |
| optimized_coefficients.csv | Primary intact OPTIMIZED and partial segment coefficients |
| identified_events.csv | All detected camera-like, Pi-like and sensor-like events, signed incremental energies and boundaries |
| model_coefficients.csv | Independent and historical reference sets |
| projections.csv | Six complete independent/reference scenario projections and counts |
| wake_requests_stable.csv, wake_requests_normal.csv, wake_requests_dynamic.csv | Simulated timestamps and wake reasons; initial manual boot is counted separately |
| activation_sensitivity.csv | Conditional count sweep |
| baseline_method_sensitivity.csv | Per-run segmentation variants |
| method_sensitivity.csv | Scenario sensitivity over segmentation variants and source segments |

The five figures are emitted as fig1_baseline_trace, fig2_optimized_trace, fig3_projected_energy, fig4_cumulative and fig5_sensitivity (.png and .svg). The measured plots are historical traces; the latter three are model projections. This is analysis documentation only; no runtime implementation changes, physical evidence or new measured energy is claimed.
