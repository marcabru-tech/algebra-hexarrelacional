"""
gurumatrix/tensor.py — The 5-Dimensional Significance Tensor G(i,j,k,t,l).

Theoretical basis (§0.4 of the original work):
    The GuruMatrix is a tensor of order 5 that catalogues computational
    patterns across five ontological dimensions:

        i  Ontological Category  — what *kind* of entity the pattern is
        j  Semantic Field        — the domain of meaning it operates in
        k  Hermeneutic Level     — the depth of interpretive engagement
        t  Execution Time        — temporal/complexity class
        l  Target Language       — the concrete realisation language

    A cell G[i,j,k,t,l] stores a pattern-significance value ∈ ℝ≥0 that
    can be used to look up canonical transformation templates or to
    compute the *distance* between two languages/domains within the
    significance space.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Dict, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Dimension enumerations
# ---------------------------------------------------------------------------

class OntologicalCategory(IntEnum):
    """Coarse ontological classification of a computational pattern."""
    DECLARATIVE = 0
    ITERATIVE = 1
    RECURSIVE = 2
    CONCURRENT = 3
    REACTIVE = 4


class SemanticField(IntEnum):
    """Broad semantic domain of the algorithm."""
    MATHEMATICS = 0
    DATA_STRUCTURES = 1
    IO_OPERATIONS = 2
    CONTROL_FLOW = 3
    METAPROGRAMMING = 4


class HermeneuticLevel(IntEnum):
    """Depth of interpretive engagement with the source text."""
    SYNTACTIC = 0      # surface structure only
    SEMANTIC = 1       # meaning of individual constructs
    PRAGMATIC = 2      # intent and use-context
    METALINGUISTIC = 3 # discourse about the language itself
    ONTOLOGICAL = 4    # fundamental category of being


class ExecutionTime(IntEnum):
    """Rough complexity class used as a temporal dimension."""
    CONSTANT = 0    # O(1)
    LOGARITHMIC = 1 # O(log n)
    LINEAR = 2      # O(n)
    POLYNOMIAL = 3  # O(n^k), k > 1
    EXPONENTIAL = 4 # O(k^n)


class TargetLanguage(IntEnum):
    """Target language for transpilation."""
    PYTHON = 0
    JAVASCRIPT = 1
    TYPESCRIPT = 2
    RUST = 3
    PSEUDOCODE = 4


# Shorthand shape
_SHAPE: Tuple[int, int, int, int, int] = (
    len(OntologicalCategory),
    len(SemanticField),
    len(HermeneuticLevel),
    len(ExecutionTime),
    len(TargetLanguage),
)


# ---------------------------------------------------------------------------
# GuruMatrix
# ---------------------------------------------------------------------------

class GuruMatrix:
    """A 5-dimensional significance tensor G(i,j,k,t,l).

    Stores pattern-significance values across the five ontological
    dimensions of the Álgebra Hexarrelacional de Significância.

    Usage::

        gm = GuruMatrix()
        gm.set_pattern(
            OntologicalCategory.RECURSIVE,
            SemanticField.MATHEMATICS,
            HermeneuticLevel.SEMANTIC,
            ExecutionTime.EXPONENTIAL,
            TargetLanguage.PYTHON,
            value=0.95,
        )
        score = gm.get_pattern(
            OntologicalCategory.RECURSIVE,
            SemanticField.MATHEMATICS,
            HermeneuticLevel.SEMANTIC,
            ExecutionTime.EXPONENTIAL,
            TargetLanguage.PYTHON,
        )
        dist = gm.calculate_language_distance(TargetLanguage.PYTHON,
                                               TargetLanguage.RUST)
    """

    def __init__(self, initialise: bool = True) -> None:
        """Initialise the 5D tensor.

        Args:
            initialise: When True, fill the tensor with a principled
                default distribution (smooth gradient seeded by index
                products, reflecting the intuition that more complex
                patterns have higher raw significance before π-compression).
        """
        self._tensor: np.ndarray = np.zeros(_SHAPE, dtype=np.float64)
        if initialise:
            self._default_init()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_pattern(
        self,
        ont_cat: OntologicalCategory,
        sem_field: SemanticField,
        herm_level: HermeneuticLevel,
        exec_time: ExecutionTime,
        target_lang: TargetLanguage,
    ) -> float:
        """Retrieve the significance value for a pattern coordinate.

        Args:
            ont_cat: Ontological category of the pattern.
            sem_field: Semantic field of the pattern.
            herm_level: Hermeneutic level of the pattern.
            exec_time: Execution-time complexity class.
            target_lang: Target programming language.

        Returns:
            The pattern significance score ∈ ℝ≥0.
        """
        return float(
            self._tensor[int(ont_cat), int(sem_field), int(herm_level),
                         int(exec_time), int(target_lang)]
        )

    def set_pattern(
        self,
        ont_cat: OntologicalCategory,
        sem_field: SemanticField,
        herm_level: HermeneuticLevel,
        exec_time: ExecutionTime,
        target_lang: TargetLanguage,
        value: float,
    ) -> None:
        """Set the significance value for a specific pattern coordinate.

        Args:
            ont_cat: Ontological category.
            sem_field: Semantic field.
            herm_level: Hermeneutic level.
            exec_time: Execution-time complexity class.
            target_lang: Target language.
            value: The significance score to store.

        Raises:
            ValueError: If *value* is negative.
        """
        if value < 0:
            raise ValueError(f"Pattern significance must be ≥ 0; got {value}.")
        self._tensor[int(ont_cat), int(sem_field), int(herm_level),
                     int(exec_time), int(target_lang)] = value

    def calculate_language_distance(
        self,
        lang1: TargetLanguage,
        lang2: TargetLanguage,
    ) -> float:
        """Compute the significance-space distance between two languages.

        The distance is the L2 norm between the two *language slices* of
        the tensor (all cells that share the language index), after
        flattening.  A distance of 0 means the two languages have
        identical significance profiles across all patterns; a large
        distance indicates they occupy very different regions of the
        significance space.

        Args:
            lang1: First target language.
            lang2: Second target language.

        Returns:
            Non-negative distance value (Euclidean norm of slice difference).
        """
        slice1 = self._tensor[..., int(lang1)].ravel()
        slice2 = self._tensor[..., int(lang2)].ravel()
        return float(np.linalg.norm(slice1 - slice2))

    def significance_slice(self, target_lang: TargetLanguage) -> np.ndarray:
        """Return the 4D significance sub-tensor for *target_lang*.

        Args:
            target_lang: The language dimension to extract.

        Returns:
            A 4D ``numpy.ndarray`` of shape
            ``(|OntologicalCategory|, |SemanticField|,
               |HermeneuticLevel|, |ExecutionTime|)``.
        """
        return self._tensor[..., int(target_lang)].copy()

    @property
    def shape(self) -> Tuple[int, int, int, int, int]:
        """Return the shape of the underlying tensor."""
        return _SHAPE

    @property
    def tensor(self) -> np.ndarray:
        """Read-only view of the underlying numpy array."""
        return self._tensor.view()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _default_init(self) -> None:
        """Fill the tensor with a smooth principled default distribution.

        Each cell value is a normalised product of the dimension indices
        passed through a sigmoid, reflecting the intuition that patterns
        at higher ontological and hermeneutic levels tend to carry more
        raw significance before π-compression.
        """
        for i in range(_SHAPE[0]):
            for j in range(_SHAPE[1]):
                for k in range(_SHAPE[2]):
                    for t in range(_SHAPE[3]):
                        for lang_idx in range(_SHAPE[4]):  # noqa: E741
                            product = (i + 1) * (j + 1) * (k + 1) * (t + 1) * (lang_idx + 1)
                            # Sigmoid normalisation into (0, 1)
                            self._tensor[i, j, k, t, lang_idx] = (
                                2.0 / (1.0 + np.exp(-product / 50.0)) - 1.0
                            )
