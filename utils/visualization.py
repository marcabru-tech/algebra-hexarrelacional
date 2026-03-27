"""
utils/visualization.py — Significance profile radar chart.

Provides a single public function, :func:`plot_significance_profile`, that
renders the six significance-relation scores (ρ₁–ρ₆) as a radar/spider
chart using *matplotlib*.  The chart makes the quality of a transpilation
immediately legible: a large, balanced polygon indicates high overall
significance across all six dimensions.

Dependencies:
    matplotlib>=3.8.0  (required)
"""

from __future__ import annotations

import math
from typing import Dict, Optional

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend (safe for headless envs)
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:  # pragma: no cover
    HAS_MATPLOTLIB = False


# Canonical display order and labels for the six relations
_RELATION_KEYS: list[str] = [
    "rho1_similitude",
    "rho2_homology",
    "rho3_equivalence",
    "rho4_symmetry",
    "rho5_equilibrium",
    "rho6_compensation",
]

_RELATION_LABELS: list[str] = [
    "ρ₁ Similitude",
    "ρ₂ Homologia",
    "ρ₃ Equivalência",
    "ρ₄ Simetria",
    "ρ₅ Equilíbrio",
    "ρ₆ Compensação",
]


def plot_significance_profile(
    relation_scores: Dict[str, float],
    title: str = "Perfil de Significância",
    filepath: Optional[str] = None,
) -> None:
    """Render a radar chart of the six significance-relation scores.

    Each of the six relations (ρ₁–ρ₆) occupies one axis of the chart.
    Scores are clipped to [0, 1] before plotting so that the chart always
    has a consistent scale.  A larger, rounder polygon indicates a more
    balanced and overall significant transpilation.

    Args:
        relation_scores: A mapping whose keys follow the canonical naming
            convention used throughout the codebase, e.g.::

                {
                    "rho1_similitude":   0.82,
                    "rho2_homology":     0.74,
                    "rho3_equivalence":  0.68,
                    "rho4_symmetry":     0.91,
                    "rho5_equilibrium":  0.55,
                    "rho6_compensation": 0.63,
                }

            Unknown keys are silently ignored; missing canonical keys
            default to 0.0.
        title: Title displayed above the chart.
        filepath: If provided, the chart is saved to this path (e.g.
            ``"profile.png"``).  When *None*, :func:`matplotlib.pyplot.show`
            is called instead (suitable for interactive environments).

    Raises:
        ImportError: If *matplotlib* is not installed.
    """
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib is required for plot_significance_profile. "
            "Install it with: pip install matplotlib"
        )

    n = len(_RELATION_KEYS)
    # Extract scores in canonical order, defaulting missing keys to 0.0
    values = [
        float(min(max(relation_scores.get(key, 0.0), 0.0), 1.0))
        for key in _RELATION_KEYS
    ]

    # Close the polygon by repeating the first value
    values_closed = values + [values[0]]
    angles = [2 * math.pi * i / n for i in range(n)] + [0.0]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})

    # Draw gridlines at 0.2 intervals
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=7, color="grey")

    # Axis labels (relation names)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(_RELATION_LABELS, fontsize=9)

    # Plot the significance polygon
    ax.plot(angles, values_closed, linewidth=2, linestyle="solid", color="#1f77b4")
    ax.fill(angles, values_closed, alpha=0.25, color="#1f77b4")

    # Annotate each vertex with its numeric score
    for angle, value, label in zip(angles[:-1], values, _RELATION_LABELS):
        ax.annotate(
            f"{value:.2f}",
            xy=(angle, value),
            xytext=(angle, value + 0.07),
            ha="center",
            va="center",
            fontsize=8,
            color="#1f77b4",
        )

    ax.set_title(title, size=12, pad=18, fontweight="bold")
    fig.tight_layout()

    if filepath:
        fig.savefig(filepath, dpi=150, bbox_inches="tight")
    else:
        plt.show()

    plt.close(fig)
