# Transportation LP

Run:

```sh
.venv/bin/python main.py
```

Input: `Data/Data DMO Project 1.xlsx`. Override paths with `--data` and `--output`.
Resources are labelled V1–V5 in Python and the results, matching the PDF.

Scripts: `model_data.py` defines the sets and parameters;
`optimization.py` formulates and solves the LP with PuLP/CBC;
`dual_analysis.py` extracts shadow prices; `reporting.py` saves results; `visualization.py`
draws the maps. `main.py` calls them in order.

```text
results/
  solution/
    shipments.csv
    summary.json
  dual/
    shadow_prices.csv
  plots/
    network_map.png
    solution_map.png
```

The solution and dual prices use PuLP/CBC.

Shadow prices use the original RHS signs, in euros per resource unit or
equivalent handling unit.
