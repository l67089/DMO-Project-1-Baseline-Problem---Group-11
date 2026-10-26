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

Transportation costs equal the straight-line distance between locations
multiplied by a resource-specific rate in euros per unit per kilometre.
Shipments are continuous, so fractional quantities are permitted. All centres
can supply all regions directly.

The LP is formulated in **PuLP** and solved with **CBC**. The supplied dataset
produces 90 shipment variables and 48 demand, supply, and handling constraints.
The project also extracts constraint shadow prices and plots the locations
and routes used by the optimal solution.

## Input data

The default workbook is `Data/Data DMO Project 1.xlsx`.

| Sheet | Contents |
| --- | --- |
| Centres | Centre IDs, coordinates, and handling capacities |
| Regions | Region IDs and coordinates |
| Resources | Resource IDs, handling factors, and transport rates |
| Supply | Available stock for each centre/resource pair |
| Demand | Minimum requirements for each region/resource pair |

The workbook is opened read-only. Resource IDs K1–K5 are translated to V1–V5
in Python and the outputs to match the assignment PDF; Excel is not modified.

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
  dual/
    shadow_prices.csv   # RHS values, activity, slack, and shadow prices
  plots/
    network_map.png     # Logistics centres and affected regions
    solution_map.png    # Arrows showing routes with positive shipments
```

Shadow prices use the original constraint signs, in euros per resource unit
or equivalent handling unit. Both maps use the workbook's planar coordinates,
with axes in kilometres and labels matching sets L and R.
