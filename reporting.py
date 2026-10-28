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
              ["family", "target", "rhs", "activity", "slack", "binding", "shadow_price_eur_per_unit",
               "allowable_increase", "allowable_decrease", "potential_savings"])


def write_fleet(problem, shipments, model, output):
    used = shipments.sum(axis=1) @ problem.cargo_volume
    rows = [dict(
        centre_id=centre, trucks_available=float(problem.trucks_available[i]),
        capacity_per_truck=float(problem.truck_capacity[i]),
        fleet_capacity=float(problem.fleet_capacity[i]), utilized_capacity=float(used[i]),
        remaining_capacity=float(problem.fleet_capacity[i] - used[i]),
        utilization_pct=float(100 * used[i] / problem.fleet_capacity[i]) if problem.fleet_capacity[i] else None,
        shadow_price_eur_per_volume=float(model.get_constraint_by_name(f"Fleet_{centre}").pi),
    ) for i, centre in enumerate(problem.centres)]
    write_csv(output / "fleet_capacity.csv", rows)


def write_objective_sensitivity(problem, shipments, costs, objective_ranges, output):
    """Save one-at-a-time ranges for the objective's shipment unit costs."""
    rows = []
    for i, centre in enumerate(problem.centres):
        for j, region in enumerate(problem.regions):
            for k, resource in enumerate(problem.resources):
                ranges = objective_ranges[centre, region, resource]
                cost = float(costs[i, j, k])
                rows.append(dict(
                    centre_id=centre, region_id=region, resource_id=resource,
                    units=float(shipments[i, j, k]), cost_eur_per_unit=cost,
                    **ranges,
                    minimum_cost_eur_per_unit=cost - ranges["allowable_decrease"],
                    maximum_cost_eur_per_unit=cost + ranges["allowable_increase"],
                ))
    write_csv(output / "objective_coefficients.csv", rows)
