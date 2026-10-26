"""Plot the network using the same planar kilometre coordinates as the LP."""

from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

from model_data import Problem
from optimization import TOLERANCE


def plot_network(problem: Problem, output: Path, shipments=None) -> Path:
    """Save a PNG with L/R markers, a legend and coordinate axes in kilometres.

    Equal axis scales preserve Euclidean geometry. Rendering uses a file-based
    canvas so running main.py does not require a desktop or open a GUI window.
    If shipments is supplied, also draw one arrow per used centre-region route
    and save the plot separately as solution_map.png.
    """
    output.mkdir(parents=True, exist_ok=True)
    figure = Figure(figsize=(6, 8), facecolor="white")
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(111)

    if shipments is not None:
        # One connection if any resource is shipped on this route. Different
        # resources have different units, so route widths are kept equal.
        for i, origin in enumerate(problem.centre_xy):
            for j, destination in enumerate(problem.region_xy):
                if (shipments[i, j] > TOLERANCE).any():
                    axes.add_patch(FancyArrowPatch(
                        origin, destination, arrowstyle="-|>",
                        mutation_scale=11, linewidth=1.2, color="#78838c",
                        shrinkA=6, shrinkB=5, zorder=2,
                    ))

    centre_colour = "#ba4b25"
    region_colour = "#236b9b"
    axes.scatter(*problem.centre_xy.T, s=135, marker="s", color=centre_colour,
                 edgecolors="white", linewidths=1.3, zorder=3,
                 label="L: Logistics centres")
    axes.scatter(*problem.region_xy.T, s=90, marker="o", color=region_colour,
                 edgecolors="white", linewidths=1.3, zorder=3,
                 label="R: Affected regions")

    for ids, xy, colour, offset, alignment in (
        (problem.centres, problem.centre_xy, centre_colour, (-10, -5), "right"),
        (problem.regions, problem.region_xy, region_colour, (10, 5), "left"),
    ):
        for location_id, point in zip(ids, xy):
            axes.annotate(location_id, point, xytext=offset, textcoords="offset points",
                          ha=alignment, va="center", fontsize=11, color=colour,
                          zorder=4)

    # Leave room for labels while retaining equal distances on both axes.
    axes.margins(x=0.2, y=0.08)
    axes.set_aspect("equal", adjustable="box")
    axes.set_xlabel("x (km)")
    axes.set_ylabel("y (km)")
    axes.set_axisbelow(True)
    axes.grid(color="#e5e5e5", linewidth=0.6)
    handles, _ = axes.get_legend_handles_labels()
    if shipments is not None:
        handles.append(Line2D([], [], color="#78838c", linewidth=1.2,
                              label="Used routes (L → R)"))
    axes.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.02),
                ncol=2, frameon=False, fontsize=10)

    png_path = output / ("solution_map.png" if shipments is not None else "network_map.png")
    figure.savefig(png_path, dpi=200, bbox_inches="tight", pad_inches=0.15)
    figure.clear()
    return png_path
