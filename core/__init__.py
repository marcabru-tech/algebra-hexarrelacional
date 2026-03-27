"""
core — The algebraic heart of π√f(A): Álgebra Hexarrelacional de Significância.

Exports the π-radical operator, the five operative modes (functors), and
the six significance relations.
"""

from .operator import pi_radical_significance, iterate_convergence
from .modes import Operacionalizar, Processar, Distribuir, Inferir, Incidir
from .relations import (
    calculate_similitude,
    calculate_homology,
    calculate_equivalence,
    calculate_symmetry,
    calculate_equilibrium,
    calculate_compensation,
)

__all__ = [
    "pi_radical_significance",
    "iterate_convergence",
    "Operacionalizar",
    "Processar",
    "Distribuir",
    "Inferir",
    "Incidir",
    "calculate_similitude",
    "calculate_homology",
    "calculate_equivalence",
    "calculate_symmetry",
    "calculate_equilibrium",
    "calculate_compensation",
]
