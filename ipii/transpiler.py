"""
ipii/transpiler.py — SemanticTranspiler: IPII orchestration engine.

Theoretical basis (§0.4 — IPII):
    IPII (Interação Paramétrica Iterativa por Interoperabilidade) is a
    protocol that implements the evaluation function f in the concrete
    domain of source-to-source transpilation.  It orchestrates the five
    operative modes (𝕆, ℙ, 𝔻, 𝕀, ℕ) in an iterative refinement loop,
    evaluates each iteration with the six significance relations, and
    returns the π-radical significance score Π(A) alongside the final
    transpiled code.

    The iterative loop refines the transpilation until either:
        (a) the score Π(A) converges (Δ < tolerance), or
        (b) the maximum number of iterations is reached.

    On each iteration the candidate with the highest relation-weighted
    score is selected, so the pipeline converges toward the most
    semantically faithful translation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from core.modes import (
    Operacionalizar,
    Processar,
    Distribuir,
    Inferir,
    Incidir,
    TranslationCandidate,
)
from core.operator import pi_radical_significance
from core.relations import (
    calculate_similitude,
    calculate_homology,
    calculate_equivalence,
    calculate_symmetry,
    calculate_equilibrium,
    calculate_compensation,
)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class TranspilationResult:
    """The full output of a :class:`SemanticTranspiler` run."""

    source_code: str
    target_lang: str
    final_code: str
    f_A: float          # raw significance score before π-radical
    pi_A: float         # Π(A) = f_A^(1/π)  — the significance score
    iterations: int
    history: List[float] = field(default_factory=list)  # f_A per iteration
    relation_scores: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# SemanticTranspiler
# ---------------------------------------------------------------------------

class SemanticTranspiler:
    """Orchestrates IPII to transpile Python source into a target language.

    The transpiler executes the five operative modes (𝕆 → ℙ → 𝔻 → 𝕀 → ℕ)
    in an iterative loop, evaluating the quality of each candidate
    translation using the six significance relations (ρ₁–ρ₆) and updating
    the candidate pool until convergence.

    Args:
        max_iterations: Maximum number of refinement iterations.
        tolerance: Convergence threshold — stop when |Π(n) - Π(n-1)| < tol.
        scorer: Optional external callable ``scorer(candidate) -> float``
                (e.g. an LLM wrapper) used by :class:`Inferir`.  When
                *None* the built-in heuristic is used.

    Example::

        transpiler = SemanticTranspiler(max_iterations=5)
        result = transpiler.transpile(
            source_code=\"\"\"
        def factorial(n: int) -> int:
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        \"\"\",
            target_lang="javascript",
        )
        print(result.final_code)
        print(f"Π(A) = {result.pi_A:.6f}")
    """

    def __init__(
        self,
        max_iterations: int = 5,
        tolerance: float = 1e-4,
        scorer: Optional[Any] = None,
    ) -> None:
        self.max_iterations = max_iterations
        self.tolerance = tolerance

        # Instantiate the five operative modes
        self._O = Operacionalizar()
        self._P = Processar()
        self._D = Distribuir()
        self._I = Inferir(scorer=scorer)
        self._N = Incidir()

    def transpile(
        self,
        source_code: str,
        target_lang: str = "javascript",
    ) -> TranspilationResult:
        """Transpile *source_code* into *target_lang* via IPII.

        Args:
            source_code: Valid Python 3 source to transpile.
            target_lang: The name of the target language (e.g. "javascript",
                         "rust", "pseudocode").

        Returns:
            A :class:`TranspilationResult` containing the transpiled code,
            the raw f(A) score, and the π-radical significance Π(A).

        Raises:
            SyntaxError: If *source_code* is not valid Python.
        """
        # ── 𝕆  Operacionalizar ─────────────────────────────────────────
        enriched = self._O(source_code)

        # ── ℙ  Processar ───────────────────────────────────────────────
        state = self._P(enriched)

        prev_pi: float = 0.0
        history: List[float] = []
        best_code: str = source_code
        best_f_A: float = 1.0
        best_candidate: Optional[TranslationCandidate] = None

        for iteration in range(self.max_iterations):
            # ── 𝔻  Distribuir ──────────────────────────────────────────
            candidates = self._D(state, target_langs=[target_lang, "pseudocode"])

            # Weight candidates by the six significance relations against
            # the original source before handing them to Inferir
            for c in candidates:
                c.score = self._relation_score(source_code, c.code_sketch)

            # ── 𝕀  Inferir ─────────────────────────────────────────────
            best_candidate = self._I(candidates)

            # ── ℕ  Incidir ─────────────────────────────────────────────
            code, f_A = self._N(best_candidate)

            # Apply the π-radical operator
            pi_A = pi_radical_significance(f_A)
            history.append(pi_A)

            # Check convergence
            if abs(pi_A - prev_pi) < self.tolerance and iteration > 0:
                best_code = code
                best_f_A = f_A
                break

            prev_pi = pi_A
            best_code = code
            best_f_A = f_A

            # Refine: feed the best candidate back into Processar
            # by re-parsing the generated sketch
            try:
                enriched = self._O(best_candidate.code_sketch)
                state = self._P(enriched)
            except SyntaxError:
                # Sketch may not be valid Python — keep current state
                pass

        final_pi = pi_radical_significance(best_f_A)
        relation_scores = self._full_relation_profile(source_code, best_code)

        return TranspilationResult(
            source_code=source_code,
            target_lang=target_lang,
            final_code=best_code,
            f_A=best_f_A,
            pi_A=final_pi,
            iterations=len(history),
            history=history,
            relation_scores=relation_scores,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _relation_score(source: str, candidate_code: str) -> float:
        """Compute a weighted average of the six significance relations."""
        weights = [0.05, 0.10, 0.20, 0.25, 0.40, 0.00]
        scores = [
            calculate_similitude(source, candidate_code),
            calculate_homology(source, candidate_code),
            calculate_equivalence(source, candidate_code),
            calculate_symmetry(source, candidate_code),
            calculate_equilibrium(source, candidate_code),
            calculate_compensation(source, candidate_code),
        ]
        return sum(w * s for w, s in zip(weights, scores))

    @staticmethod
    def _full_relation_profile(source: str, result: str) -> dict:
        """Return a named dict of all six relation scores."""
        return {
            "rho1_similitude": calculate_similitude(source, result),
            "rho2_homology": calculate_homology(source, result),
            "rho3_equivalence": calculate_equivalence(source, result),
            "rho4_symmetry": calculate_symmetry(source, result),
            "rho5_equilibrium": calculate_equilibrium(source, result),
            "rho6_compensation": calculate_compensation(source, result),
        }
