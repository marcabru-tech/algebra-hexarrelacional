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

from dataclasses import dataclass, field
from typing import Any, List, Optional

from core.modes import (
    Operacionalizar,
    Processar,
    Distribuir,
    Inferir,
    Incidir,
    LLMScorer,
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
                (e.g. an :class:`~core.modes.LLMScorer` instance) used by
                :class:`~core.modes.Inferir`.  When *None* the built-in
                heuristic is used.
        llm_client: Optional OpenAI-compatible client.  When provided
                (and *scorer* is *None*), an :class:`~core.modes.LLMScorer`
                is constructed automatically for each :meth:`transpile` call
                using the supplied client, the source code, and the target
                language.
        guru_matrix: Optional :class:`~gurumatrix.tensor.GuruMatrix`
                instance.  When provided, :meth:`transpile` calls
                :meth:`~gurumatrix.tensor.GuruMatrix.learn_from_transpilation`
                after each successful run so the tensor adapts over time.
        visualization_filepath: Optional path template for saving radar
                charts.  When provided, a significance-profile radar chart
                is saved after each :meth:`transpile` call.  The substring
                ``"{target_lang}"`` inside the template is replaced with
                the actual target language name.

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
        llm_client: Optional[Any] = None,
        guru_matrix: Optional[Any] = None,
        visualization_filepath: Optional[str] = None,
    ) -> None:
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self._explicit_scorer = scorer
        self._llm_client = llm_client
        self._guru_matrix = guru_matrix
        self._visualization_filepath = visualization_filepath

        # Instantiate the five operative modes.
        # Inferir is re-instantiated per transpile() call when an LLM client
        # is present so it can bind the source code and target language.
        self._O = Operacionalizar()
        self._P = Processar()
        self._D = Distribuir()
        self._N = Incidir()
        # Default Inferir (may be overridden per call when LLM is active)
        self._I = Inferir(scorer=self._explicit_scorer)

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
        # Resolve scorer: explicit > LLM client > heuristic
        if self._explicit_scorer is not None:
            inferir = self._I
        elif self._llm_client is not None:
            llm_scorer = LLMScorer(
                self._llm_client, source_code, target_lang
            )
            inferir = Inferir(scorer=llm_scorer)
        else:
            inferir = self._I

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
            best_candidate = inferir(candidates)

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

        result = TranspilationResult(
            source_code=source_code,
            target_lang=target_lang,
            final_code=best_code,
            f_A=best_f_A,
            pi_A=final_pi,
            iterations=len(history),
            history=history,
            relation_scores=relation_scores,
        )

        # ── Post-processing: visualisation ─────────────────────────────
        if self._visualization_filepath:
            try:
                from utils.visualization import plot_significance_profile  # noqa: E402
                filepath = self._visualization_filepath.replace(
                    "{target_lang}", target_lang
                )
                plot_significance_profile(
                    relation_scores,
                    title=f"Perfil de Significância — Python → {target_lang}",
                    filepath=filepath,
                )
            except Exception:  # noqa: BLE001
                pass  # visualisation is non-critical

        # ── Post-processing: GuruMatrix learning ───────────────────────
        if self._guru_matrix is not None:
            try:
                self._guru_matrix.learn_from_transpilation(
                    source_ast=enriched,
                    target_ast=best_code,
                    target_lang=target_lang,
                    pi_score=final_pi,
                    relation_scores=relation_scores,
                )
            except Exception:  # noqa: BLE001
                pass  # learning is non-critical

        return result

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
