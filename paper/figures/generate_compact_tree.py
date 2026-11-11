"""Render the manuscript's compact, printable decision tree."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent


def box(ax, x, y, w, h, label, *, gate=False):
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.035,rounding_size=0.06",
        linewidth=0.8,
        edgecolor="#283747",
        facecolor="#eaf1f8" if gate else "#f8f9fa",
    )
    ax.add_patch(patch)
    ax.text(x, y, label, ha="center", va="center", fontsize=7.2 if gate else 6.9)


def arrow(ax, start, end, label=None, label_offset=(0, 0)):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=0.8,
            color="#283747",
            connectionstyle="arc3,rad=0",
        )
    )
    if label:
        ax.text(
            (start[0] + end[0]) / 2 + label_offset[0],
            (start[1] + end[1]) / 2 + label_offset[1],
            label,
            ha="center",
            va="center",
            fontsize=6.2,
            color="#34495e",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.7},
        )


def main():
    fig, ax = plt.subplots(figsize=(7.15, 1.72))
    fig.patch.set_facecolor("white")
    ax.set_xlim(-0.15, 10.15)
    ax.set_ylim(0, 4.25)
    ax.axis("off")

    gates = [
        (1.05, "1. Valid occurrence\nand commit evidence?"),
        (3.55, "2. Object type\nand repository scope?"),
        (6.05, "3. File exists at\nanchor after resolution?"),
        (8.55, "4. Intent of the\nabsent local file?"),
    ]
    for x, label in gates:
        box(ax, x, 3.55, 2.05, 0.75, label, gate=True)

    for left, right, label in (
        (2.11, 2.48, "verifiable"),
        (4.61, 4.98, "local file"),
        (7.11, 7.48, "absent"),
    ):
        arrow(ax, (left, 3.55), (right, 3.55), label, (0, 0.24))

    box(ax, 1.05, 1.24, 1.85, 0.68, "Inaccessible\nor invalid")
    arrow(ax, (1.05, 3.15), (1.05, 1.60), "no", (-0.14, 0))

    box(ax, 3.60, 2.00, 1.85, 0.62, "Non-file reference")
    box(ax, 3.60, 0.95, 1.85, 0.62, "External repository")
    ax.plot([3.55, 3.55, 2.40, 2.40], [3.15, 2.80, 2.80, 0.95], color="#283747", lw=0.8)
    arrow(ax, (2.40, 2.00), (2.64, 2.00))
    arrow(ax, (2.40, 0.95), (2.64, 0.95))

    box(ax, 6.05, 1.24, 1.85, 0.68, "Confirmed exists\nat anchor")
    arrow(ax, (6.05, 3.15), (6.05, 1.60), "yes", (-0.16, 0))

    leaves = [
        (8.73, 2.55, "Expected creation"),
        (8.73, 1.85, "Expected move or deletion"),
        (8.73, 1.15, "Confirmed problematic\nabsence"),
        (8.73, 0.45, "Ambiguous: insufficient\nevidence"),
    ]
    for x, y, label in leaves:
        box(ax, x, y, 2.12, 0.59, label)
    ax.plot([8.55, 8.55, 7.35, 7.35], [3.15, 2.94, 2.94, 0.45], color="#283747", lw=0.8)
    for _, y, _ in leaves:
        arrow(ax, (7.35, y), (7.64, y))

    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(HERE / "decision_tree_compact.pdf", transparent=False)
    fig.savefig(HERE / "decision_tree_compact.svg", transparent=False)
    plt.close(fig)


if __name__ == "__main__":
    main()
