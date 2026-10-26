"""Save numerical results to CSV and JSON."""

import csv
import json


def write_csv(path, rows, columns=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_results(problem, x, distances, costs, summary, output):
    rows = [dict(centre_id=centre, region_id=region, resource_id=resource,
                 units=float(x[i, j, k]), distance_km=float(distances[i, j]),
                 cost_eur_per_unit=float(costs[i, j, k]),
                 total_cost_eur=float(costs[i, j, k] * x[i, j, k]))
            for i, centre in enumerate(problem.centres)
            for j, region in enumerate(problem.regions)
            for k, resource in enumerate(problem.resources)]
    write_csv(output / "shipments.csv", rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_dual(dual, output):
    write_csv(output / "shadow_prices.csv", dual,
              ["family", "target", "rhs", "activity", "slack", "binding", "shadow_price_eur_per_unit"])
