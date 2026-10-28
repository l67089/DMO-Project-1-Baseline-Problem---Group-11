"""Analyze the dual values of the solved transportation LP. hello"""

from optimization import TOLERANCE


def constraint_metadata(problem):
    """List the names, locations and RHS values of the model's constraints."""
    rows = []
    # Demand is indexed by region/resource; supply by centre/resource.
    for family, values, ids in (("demand", problem.demand, problem.regions),
                                ("supply", problem.supply, problem.centres)):
        for first, location in enumerate(ids):
            for k, resource in enumerate(problem.resources):
                # Example: Demand_R1_V1, with RHS 110 and array position (0, 0).
                # Names must match those assigned to constraints in optimization.py.
                rows.append(dict(family=family, target=f"{location}/{resource}",
                                 rhs=float(values[first, k]),
                                 constraint_name=f"{family.title()}_{location}_{resource}"))
    for i, centre in enumerate(problem.centres):
        # Capacity has one value per centre.
        rows.append(dict(family="capacity", target=centre, rhs=float(problem.capacity[i]),
                         constraint_name=f"Capacity_{centre}"))
    for i, centre in enumerate(problem.centres):
        # Fleet shadow prices are euros per extra cargo-space unit.
        rows.append(dict(family="fleet", target=centre, rhs=float(problem.fleet_capacity[i]),
                         constraint_name=f"Fleet_{centre}"))
    return rows


def analyze_dual(problem, model, rhs_ranges):
    """Read shadow prices and allowable RHS changes from the solved LP."""
    # problem holds the inputs; model holds the solved LP.
    constraints = []
    for metadata in constraint_metadata(problem):
        # Retrieve the solved constraint using its name, e.g. Supply_L1_V1.
        constraint = model.get_constraint_by_name(metadata["constraint_name"])

        # pi is the solver's chosen shadow price: the local objective change
        # per extra RHS unit when that dual value remains applicable.
        # Demand uses >= and stock/capacity use <= directly in the PuLP model,
        # so these prices already have the signs of the original PDF model.
        price = float(constraint.pi)

        # Report nonnegative slack consistently:
        # demand slack = deliveries - requirement (surplus);
        # supply/capacity slack = availability - usage (unused amount).
        # CBC reports demand surplus with the opposite sign, so reverse it.
        slack = float(-constraint.slack if metadata["family"] == "demand" else constraint.slack)

        # Activity is the constraint's left-hand side: deliveries, dispatches
        # or weighted handling use. Recover it from the RHS and the slack.
        activity = metadata["rhs"] + (slack if metadata["family"] == "demand" else -slack)

        # **metadata copies the identifying fields into this result dictionary.
        # Binding means there is effectively no slack, allowing numerical noise.
        entry = dict(**metadata, activity=activity,
                     slack=slack, binding=bool(slack <= TOLERANCE), shadow_price_eur_per_unit=price)
        # Both allowances refer to this original RHS, with all others fixed.
        # A zero allowance can occur at a degenerate optimal basis.
        entry.update(rhs_ranges[metadata["constraint_name"]])

        constraints.append(entry)

    # reporting.py saves one row per constraint in shadow_prices.csv.
    return constraints
