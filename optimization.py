"""Formulate and solve the continuous transportation LP using the PuLP/CBC module"""

# Importing libraries.
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
    # mip=False requests a continuous LP solve, providing dual prices.
    result = model.solve(pulp.COIN_CMD(msg=False, mip=False))
    if result.status != pulp.LpSolveStatus.Optimal:
        raise RuntimeError(f"PuLP/CBC: {result.status_str}")

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
    return shipments, distances, costs, summary, model
