# Humanitarian Resource Allocation — Transportation LP

This project implements the humanitarian transportation problem from the
Decision Making and Optimization assignment. It determines how much of each
resource to send from logistics centres to affected regions while minimising
total transportation cost.

The supplied dataset contains three logistics centres (L1–L3), six affected
regions (R1–R6), and five resources (V1–V5): drinking water, food parcels,
medical kits, shelter kits, and hygiene kits.

## The model

Each decision variable represents the quantity of one resource shipped from
one centre to one region. The model must:

- Meet every region's minimum demand for each resource.
- Keep dispatches within each centre's available resource stock.
- Respect each centre's handling capacity, accounting for the different
  handling effort required by each resource.
- Keep total dispatched cargo volume within the capacity of each centre's
  available truck fleet.

Transportation costs equal the straight-line distance between locations
multiplied by a resource-specific rate in euros per unit per kilometre.
Shipments are continuous, so fractional quantities are permitted. All centres
can supply all regions directly.

The LP is formulated in **PuLP** and solved with **CBC**. The supplied dataset
produces 90 continuous shipment variables and 51 demand, supply, handling,
and fleet constraints. There are no truck assignment or integer variables.
The project also extracts constraint shadow prices and plots the locations
and routes used by the optimal solution.

## Input data

The default workbook is `Data/Data DMO Project 1 Updated.xlsx`.

| Sheet | Contents |
| --- | --- |
| Centres | Centre IDs, coordinates, handling capacity, `trucks_available`, `truck_capacity`, and `fleet_capacity` |
| Regions | Region IDs and coordinates |
| Resources | Resource IDs, handling factors, transport rates, and `cargo_volume_per_unit` |
| Supply | Available stock for each centre/resource pair |
| Demand | Minimum requirements for each region/resource pair |

The workbook is opened read-only. Resource IDs K1–K5 are translated to V1–V5
in Python and the outputs to match the assignment PDF; Excel is not modified.
The code recomputes fleet capacity as trucks available × capacity per truck
and checks the workbook's `fleet_capacity` value when present. Cargo volumes
and truck capacities use the same space units supplied in the dataset.

## Fleet constraint and dual

Let `N[i]` be available trucks, `Q[i]` capacity per truck, and `v[k]` space
per resource unit. All are fixed inputs. The added constraint is:

```text
sum(j,k) v[k] * x[i,j,k] <= F[i], where F[i] = N[i] * Q[i]
```

The original objective and all demand, stock and handling constraints remain.
With demand prices π ≥ 0 and stock, handling and fleet prices μ, ν, λ ≤ 0,
the updated dual is:

```text
max  sum(j,k) D[j,k]*π[j,k] + sum(i,k) S[i,k]*μ[i,k]
     + sum(i) C[i]*ν[i] + sum(i) F[i]*λ[i]
s.t. π[j,k] + μ[i,k] + w[k]*ν[i] + v[k]*λ[i] <= c[i,j,k]
```

Fleet prices are euros per additional cargo-space unit. They describe a local
change in the optimal transport cost; they need not remain valid for a larger
capacity change.

## Running the project

For a fresh environment, install the dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

From the project folder, run:

```sh
.venv/bin/python main.py
```

To select another workbook or results folder:

```sh
.venv/bin/python main.py --data "Data/another_workbook.xlsx" --output results
```

## Code structure

| Script | Responsibility |
| --- | --- |
| `main.py` | Runs the complete workflow |
| `model_data.py` | Loads the workbook and defines sets and parameters |
| `optimization.py` | Builds and solves the PuLP/CBC model |
| `dual_analysis.py` | Extracts constraint activity, slack, and shadow prices |
| `reporting.py` | Writes numerical results to CSV and JSON |
| `visualization.py` | Generates the location and optimal-route maps |

## Results

Each run saves the following files:

```text
results/
  solution/
    shipments.csv       # Shipment quantities, distances, and costs
    summary.json        # Solver status, objective values, and model size
    fleet_capacity.csv  # Trucks, capacity, utilized/remaining volume, utilization %, and price
  dual/
    shadow_prices.csv   # RHS values, slack, shadow prices, and allowable changes
  plots/
    network_map.png     # Logistics centres and affected regions
    solution_map.png    # Arrows showing routes with positive shipments
```

Shadow prices use the original constraint signs, in euros per resource unit,
equivalent handling unit, or cargo-space unit. Both maps use the workbook's planar coordinates,
with axes in kilometres and labels matching sets L and R.

## Allowable RHS changes

`shadow_prices.csv` includes `allowable_increase` and `allowable_decrease` for
each demand, supply, handling and fleet constraint. These come from CBC's native
RHS-ranging report and preserve its current optimal simplex basis. Change one
RHS at a time, holding all other inputs fixed. Inside the range, the objective
change is the shadow price multiplied by the RHS change; shipment quantities
can change. At the endpoints another basis may become optimal.

Allowances use the RHS units: resource quantities, equivalent handling units,
or fleet cargo-space units. They are not percentage changes or truck counts.
`inf` means no basis limit in that direction, while zero can be legitimate
for a degenerate basis. Physical inputs should still remain nonnegative.
Ranges can differ between optimal bases when multiple bases are available.

The calculation uses PuLP/CBC only. No scenario files or extra solver are added.
See the [CBC printing-options documentation](https://github.com/coin-or/Cbc/blob/master/doc/cbc-parameters.md#printingoptions).
