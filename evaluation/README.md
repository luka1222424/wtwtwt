# Energy evaluation

The comparison contains BASELINE and dynamic HALT-enabled OPTIMIZED. See [functional evaluation and equations](../docs/CURRENT_EVALUATION.md).

From the repository root:

```sh
python -m pip install -r evaluation/requirements.txt
python evaluation/analyze_current.py
```

The script replays the adaptive policy, checks the published results, and generates figures and sensitivity tables in `evaluation/current/generated/`. The input summaries in `current/` are functional measurements and model event counts, not electrical power recordings.

The original Monsoon extraction script is `analyze_energy.py`; its input CSV manifest, trace-quality results, event data and coefficients are in `data/`. The original raw measurement archives are retained separately by the authors. To reproduce their extraction, verify the original input archives against the [measurement methodology](../docs/MATHEMATICAL_CALCULATIONS.md), then run:

```sh
python evaluation/analyze_energy.py "baseline(2).zip" "optimzed(4).zip" --out characterized_power
```

The latter command reproduces power characterization and its associated historical model outputs; use `analyze_current.py` for the final 144-hour comparison.
