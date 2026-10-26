"""Run the model and save its results."""

import argparse
from pathlib import Path


from model_data import read_data
from optimization import solve
from reporting import write_dual, write_results
from visualization import plot_network
from dual_analysis import analyze_dual

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "Data" / "Data DMO Project 1.xlsx")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    problem = read_data(args.data)
    x, distances, costs, summary, model = solve(problem)
    dual = analyze_dual(problem, model)

    write_results(problem, x, distances, costs, summary, args.output / "solution")
    write_dual(dual, args.output / "dual")
    plot_network(problem, args.output / "plots")
    plot_network(problem, args.output / "plots", shipments=x)
    print(f"Optimal cost (PuLP/CBC): EUR {summary['objective_eur']:,.2f}")
    print(f"Results: {args.output.resolve()}")


if __name__ == "__main__":
    main()
