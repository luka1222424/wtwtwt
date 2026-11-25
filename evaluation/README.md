# Energy evaluation

The primary comparison contains only final BASELINE and dynamic HALT-enabled OPTIMIZED. See [current evaluation](../docs/CURRENT_EVALUATION.md).

```sh
python -m pip install -r evaluation/requirements.txt
python evaluation/analyze_current.py
```

The script independently replays the adaptive policy and verifies current CSV totals, then generates two-profile figures and sensitivity outputs under current/generated/. Historical coefficients and extraction scripts under data/ and analyze_energy.py remain provenance for the power model. The previous full research analysis (including development tests and additional simulated controls) is preserved at [d45c1f5](https://github.com/luka1222424/wtwtwt/tree/d45c1f514402bac7c8c341b9ac01e7dc46ed9542). It is not a separate set of final operating profiles.

To reproduce the original power coefficients, obtain the original baseline(2).zip and optimzed(4).zip, validate SHA-256 against [historical calculations](../docs/MATHEMATICAL_CALCULATIONS.md) and run `python evaluation/analyze_energy.py "baseline(2).zip" "optimzed(4).zip" --out historical_results`. No new power trace is claimed.
