"""Run the model and save its results."""

import argparse
from pathlib import Path

import yaml


from model_data import read_data
from optimization import solve
from reporting import write_dual, write_fleet, write_results, write_objective_sensitivity
from visualization import plot_network
from dual_analysis import analyze_dual

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yml")
    parser.add_argument("--data", type=Path, help="Override the dataset selected in config.yml")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    # A command-line dataset takes priority over the configuration file.
    if args.data is not None:
        data_path = args.data
    else:
        config_path = args.config.resolve()
        with config_path.open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        data_path = Path(config["dataset"])
        # Resolve configured paths relative to config.yml, not the terminal folder.
        if not data_path.is_absolute():
            data_path = config_path.parent / data_path

    # Label every output using the selected workbook, including --data overrides.
    suffix = "_ALTERNATIVE" if data_path.stem.upper().endswith(" ALTERNATIVE") else ""

    print(f"Dataset: {data_path.resolve()}")
    problem = read_data(data_path)
    x, distances, costs, summary, model, rhs_ranges, objective_ranges = solve(problem)
    dual = analyze_dual(problem, model, rhs_ranges)

    write_results(problem, x, distances, costs, summary, args.output / "solution", suffix=suffix)
    write_dual(dual, args.output / "dual", suffix=suffix)
    write_objective_sensitivity(problem, x, costs, objective_ranges, args.output / "sensitivity", suffix=suffix)
    write_fleet(problem, x, model, args.output / "solution", suffix=suffix)
    plot_network(problem, args.output / "plots", suffix=suffix)
    plot_network(problem, args.output / "plots", shipments=x, suffix=suffix)
    print(f"Optimal cost (PuLP/CBC): EUR {summary['objective_eur']:,.2f}")
    print(f"Results: {args.output.resolve()}")
    print("All code executed successfully. Check the results in the specified output directory.")

if __name__ == "__main__":
    main()
