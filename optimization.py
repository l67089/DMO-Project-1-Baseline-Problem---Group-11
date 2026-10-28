"""Formulate and solve the continuous transportation LP using the PuLP/CBC module"""

# Importing libraries.
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pulp

# Importing the input container built from Excel.
from model_data import Problem


TOLERANCE = 1e-7  # Used to identify positive shipments and binding constraints.


def formulate(problem: Problem):
    """Creating the PuLP LP model, shipment variables, distances and unit costs."""
    # Compute the straight-line distance between every centre and region.
    distances = np.linalg.norm(problem.centre_xy[:, None, :] - problem.region_xy[None, :, :], axis=2)
    # Unit transport cost c[i,j,k] = distance d[i,j] * rate r[k].
    costs = distances[:, :, None] * problem.rate[None, None, :]
    model = pulp.LpProblem("Humanitarian_transportation", pulp.LpMinimize)

    # One continuous, nonnegative variable for each centre/region/resource.
    # For example, x["L1", "R1", "V1"] is water shipped from L1 to R1.
    x = model.add_variable_dict(
        "x", (problem.centres, problem.regions, problem.resources),
        lowBound=0, cat=pulp.LpContinuous,
    )

    # Objective: minimise the sum of unit costs multiplied by shipment quantities.
    model += pulp.lpSum(
        float(costs[i, j, k]) * x[centre, region, resource]
        for i, centre in enumerate(problem.centres)
        for j, region in enumerate(problem.regions)
        for k, resource in enumerate(problem.resources)
    ), "Total_transport_cost"

    # Defining the constraints of the model.
    # Demand: each region must receive at least its requirement of each resource.
    for j, region in enumerate(problem.regions):
        for k, resource in enumerate(problem.resources):
            model += (
                pulp.lpSum(x[centre, region, resource] for centre in problem.centres)
                >= float(problem.demand[j, k]),
                f"Demand_{region}_{resource}",
            )

    # Supply: each centre can dispatch no more than its available stock.
    for i, centre in enumerate(problem.centres):
        for k, resource in enumerate(problem.resources):
            model += (
                pulp.lpSum(x[centre, region, resource] for region in problem.regions)
                <= float(problem.supply[i, k]),
                f"Supply_{centre}_{resource}",
            )

    # Handling: all resources dispatched by a centre share its weighted capacity.
    for i, centre in enumerate(problem.centres):
        model += (
            pulp.lpSum(float(problem.handling[k]) * x[centre, region, resource]
                       for region in problem.regions
                       for k, resource in enumerate(problem.resources))
            <= float(problem.capacity[i]),
            f"Capacity_{centre}",
        )

    # Fleet volume: sum_j sum_k v[k] * x[i,j,k] <= F[i] from Excel.
    # All shipment variables remain continuous.
    for i, centre in enumerate(problem.centres):
        model += (
            pulp.lpSum(float(problem.cargo_volume[k]) * x[centre, region, resource]
                       for region in problem.regions
                       for k, resource in enumerate(problem.resources))
            <= float(problem.fleet_capacity[i]),
            f"Fleet_{centre}",
        )

    return model, x, distances, costs


def shipment_values(problem, variables):
    # Convert PuLP values into an array indexed by centre, region and resource.
    return np.array([
        [[variables[centre, region, resource].value() for resource in problem.resources]
         for region in problem.regions] for centre in problem.centres
    ], dtype=float)


def solve(problem: Problem):
    """Build the model, solve it and return the results used by main.py."""
    model, variables, distances, costs = formulate(problem)
    # CBC reports RHS and objective-coefficient ranges for the same optimal basis.
    # Raw solver reports stay in temporary files.
    with TemporaryDirectory(prefix="dmo_rhs_") as temporary:
        report = Path(temporary) / "rhs_ranges.csv"
        objective_report = Path(temporary) / "objective_ranges.csv"
        # Match CBC's renamed columns to the original shipment variable names.
        _, _, _, column_names = model.writeMPS(str(Path(temporary) / "mapping.mps"), rename=True)
        solver = pulp.COIN_CMD(
            msg=False, mip=False, presolve=False,
            options=["initialSolve", "printingOptions rhsranging", f"solution {report}",
                     "printingOptions objectiveranging", f"solution {objective_report}"],
        )
        result = model.solve(solver)
        if result.status != pulp.LpSolveStatus.Optimal:
            raise RuntimeError(f"PuLP/CBC: {result.status_str}")
        constraints = model.constraints()
        rhs_ranges = {}
        with report.open(newline="") as stream:
            rows = csv.reader(stream)
            next(rows)  # Native report header: row, name, increase, ..., decrease, ...
            for row in rows:
                index = int(row[0])
                # PuLP writes MPS rows in this order, renamed C0000000, etc.
                if row[1] != f"C{index:07d}":
                    raise RuntimeError("Unexpected CBC constraint name in RHS-ranging report")
                increase, decrease = float(row[2]), float(row[4])
                rhs_ranges[constraints[index].name] = dict(
                    allowable_increase=float("inf") if increase >= 1e99 else max(0., increase),
                    allowable_decrease=float("inf") if decrease >= 1e99 else max(0., decrease),
                )
        if len(rhs_ranges) != model.numConstraints():
            raise RuntimeError("CBC did not report RHS ranges for every constraint")

        objective_ranges = {}
        with objective_report.open(newline="") as stream:
            rows = csv.reader(stream)
            next(rows)
            for row in rows:
                index = int(row[0])
                if row[1] != f"X{index:07d}":
                    raise RuntimeError("Unexpected CBC variable name in objective-ranging report")
                increase, decrease = float(row[2]), float(row[4])
                objective_ranges[column_names[index]] = dict(
                    allowable_increase=float("inf") if increase >= 1e99 else max(0., increase),
                    allowable_decrease=float("inf") if decrease >= 1e99 else max(0., decrease),
                )
        if len(objective_ranges) != len(variables):
            raise RuntimeError("CBC did not report objective ranges for every shipment variable")
        # Use the original (centre, region, resource) keys in the output writer.
        objective_ranges = {key: objective_ranges[var.name] for key, var in variables.items()}

    shipments = shipment_values(problem, variables)
    summary = {
        "status": result.status_str,
        "solver": "PuLP / CBC",
        "objective_eur": float(pulp.value(model.objective)),
        "dual_objective_eur": float(sum(-row.constant * row.pi for row in model.constraints())),
        "variables": int(shipments.size),
        "functional_constraints": model.numConstraints(),
        "positive_shipments": int(np.count_nonzero(shipments > TOLERANCE)),
    }
    return shipments, distances, costs, summary, model, rhs_ranges, objective_ranges
