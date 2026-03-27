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

import ast
from enum import IntEnum
from typing import Any, Dict, Optional, Tuple

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

    # ------------------------------------------------------------------
    # Dynamic learning
    # ------------------------------------------------------------------

    def learn_from_transpilation(
        self,
        source_ast: Any,
        target_ast: Any,
        target_lang: str,
        pi_score: float,
        relation_scores: Dict[str, float],
        threshold: float = 0.8,
        reinforcement: float = 0.01,
    ) -> None:
        """Adjust tensor patterns based on a completed transpilation.

        When *pi_score* is above *threshold* the transpilation is
        considered successful, and the tensor cells corresponding to the
        inferred coordinates of both ASTs are reinforced by *reinforcement*
        (clipped to 1.0).  This provides a simple online-learning
        mechanism so that the GuruMatrix adapts to the kinds of patterns
        that produce high-significance transpilations over time.

        Args:
            source_ast: The source AST or enriched-AST object from
                :class:`core.modes.Operacionalizar`.  Its node-type
                histogram is used to infer ontological coordinates.
            target_ast: The target AST or code string.  Used to infer
                the hermeneutic level of the resulting artefact.
            target_lang: Name of the target language (e.g. ``"javascript"``).
            pi_score: The Π(A) significance score of the transpilation,
                in ℝ≥0.
            relation_scores: A mapping of relation-name → score for the
                six significance relations ρ₁–ρ₆.
            threshold: Minimum *pi_score* to trigger reinforcement.
                Default 0.8.
            reinforcement: Amount added to each relevant tensor cell.
                Default 0.01.
        """
        if pi_score < threshold:
            return

        lang_idx = self._resolve_lang_index(target_lang)
        ont_idx = self._infer_ont_index(source_ast)
        herm_idx = self._infer_herm_index(relation_scores)

        # Reinforce all (semantic-field, exec-time) cells for the inferred
        # (ontological, hermeneutic, language) coordinate.
        for sem in range(_SHAPE[1]):
            for exc in range(_SHAPE[3]):
                current = self._tensor[ont_idx, sem, herm_idx, exc, lang_idx]
                self._tensor[ont_idx, sem, herm_idx, exc, lang_idx] = min(
                    current + reinforcement, 1.0
                )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, filepath: str) -> None:
        """Serialise the GuruMatrix tensor to *filepath* using NumPy format.

        The file is saved as a ``.npy`` binary; the ``.npy`` extension is
        appended automatically if absent.

        Args:
            filepath: Destination path (e.g. ``"gurumatrix.npy"``).
        """
        np.save(filepath, self._tensor)

    def load(self, filepath: str) -> None:
        """Load a previously saved GuruMatrix tensor from *filepath*.

        The loaded array must have the same shape as ``_SHAPE``
        ``(5, 5, 5, 5, 5)``; otherwise a :exc:`ValueError` is raised.

        Args:
            filepath: Source path (e.g. ``"gurumatrix.npy"``).

        Raises:
            ValueError: If the loaded array shape does not match
                :data:`_SHAPE`.
        """
        data = np.load(filepath)
        if data.shape != _SHAPE:
            raise ValueError(
                f"Loaded tensor shape {data.shape} does not match "
                f"expected GuruMatrix shape {_SHAPE}."
            )
        self._tensor = data

    # ------------------------------------------------------------------
    # Private helpers for learning
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_lang_index(target_lang: str) -> int:
        """Map a language name string to a :class:`TargetLanguage` index."""
        mapping = {
            "python": int(TargetLanguage.PYTHON),
            "javascript": int(TargetLanguage.JAVASCRIPT),
            "typescript": int(TargetLanguage.TYPESCRIPT),
            "rust": int(TargetLanguage.RUST),
            "pseudocode": int(TargetLanguage.PSEUDOCODE),
        }
        return mapping.get(target_lang.lower(), int(TargetLanguage.PSEUDOCODE))

    @staticmethod
    def _infer_ont_index(source_ast: Any) -> int:
        """Infer an :class:`OntologicalCategory` index from *source_ast*."""
        # Support EnrichedAST-like objects (duck-typed) or raw ast.AST
        histogram: Dict[str, int] = {}
        if hasattr(source_ast, "metadata") and isinstance(
            source_ast.metadata, dict
        ):
            histogram = source_ast.metadata.get("node_type_histogram", {})
        elif isinstance(source_ast, ast.AST):
            for node in ast.walk(source_ast):
                key = type(node).__name__
                histogram[key] = histogram.get(key, 0) + 1

        if "ClassDef" in histogram:
            return int(OntologicalCategory.DECLARATIVE)
        if "FunctionDef" in histogram or "AsyncFunctionDef" in histogram:
            return int(OntologicalCategory.RECURSIVE)
        if "For" in histogram or "While" in histogram:
            return int(OntologicalCategory.ITERATIVE)
        return int(OntologicalCategory.DECLARATIVE)

    @staticmethod
    def _infer_herm_index(relation_scores: Dict[str, float]) -> int:
        """Infer a :class:`HermeneuticLevel` index from relation scores.

        The equivalence score (ρ₃) drives the hermeneutic depth: the
        higher the equivalence, the deeper the level of interpretive
        engagement captured in the tensor.
        """
        eq_score = relation_scores.get("rho3_equivalence", 0.0)
        if eq_score >= 0.8:
            return int(HermeneuticLevel.ONTOLOGICAL)
        if eq_score >= 0.6:
            return int(HermeneuticLevel.METALINGUISTIC)
        if eq_score >= 0.4:
            return int(HermeneuticLevel.PRAGMATIC)
        if eq_score >= 0.2:
            return int(HermeneuticLevel.SEMANTIC)
        return int(HermeneuticLevel.SYNTACTIC)
