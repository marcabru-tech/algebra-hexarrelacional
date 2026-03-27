"""
core/modes.py — The Five Operative Modes (Functors) of the function f.

Theoretical basis (§0.2 of the original work):
    The evaluation function f acts on algorithm A through five distinct
    modes that form a communicating network:

        𝕆  Operacionalizar  — bring the algorithm into the real domain
        ℙ  Processar        — transform it step-by-step
        𝔻  Distribuir       — spread the result across domains/nodes
        𝕀  Inferir          — derive implicit consequences
        ℕ  Incidir          — project the inference onto the world (causal)

Each mode is implemented as a callable class (functor) with a unified
``__call__`` interface so that they can be composed in any order or
networked topology.
"""

from __future__ import annotations

import ast
import json
import logging
import math
import hashlib
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Shared domain types
# ---------------------------------------------------------------------------

@dataclass
class EnrichedAST:
    """A Python AST node augmented with ontological and semantic metadata."""

    tree: ast.AST
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntermediateState:
    """The symbolic state produced after the Processar step."""

    source_code: str
    node_count: int
    depth: int
    node_types: Dict[str, int]
    enriched_ast: EnrichedAST
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationCandidate:
    """A single candidate translation/transpilation produced by Distribuir."""

    target_lang: str
    code_sketch: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# LLM-based scorer (used by Inferir when an llm_client is provided)
# ---------------------------------------------------------------------------

_logger = logging.getLogger(__name__)

_LLM_PROMPT_TEMPLATE = """\
You are an expert in programming language semantics and code transpilation.

Evaluate the quality of the following transpilation candidate from Python to {target_lang}.

## Original Python source
```python
{source_code}
```

## Transpilation candidate ({target_lang})
```
{candidate_code}
```

Score this candidate on a scale from 0.0 to 1.0, considering:
- ρ₁ Similitude: surface similarity of vocabulary and structure
- ρ₂ Homologia: structural isomorphism (same control-flow shape)
- ρ₃ Equivalência: functional substitutability (same observable behaviour)
- ρ₄ Simetria: reversibility of the transformation
- ρ₅ Equilíbrio: mutual complementarity between source and target
- ρ₆ Compensação: emergent value — the target improves on the source idiomatically

Respond ONLY with a JSON object in the following format (no extra text):
{{"score": <float 0.0–1.0>, "justification": "<one sentence>"}}
"""


class LLMScorer:
    """Wrap an OpenAI-compatible LLM client as a :class:`Inferir` scorer.

    The scorer calls the LLM with a structured prompt that describes the
    original source code, the transpilation candidate, and the six
    significance relations.  The LLM is instructed to return a JSON
    object ``{"score": float, "justification": str}``; only the numeric
    score is used to rank candidates.

    If the LLM is unavailable or returns an unparseable response, the
    scorer falls back silently to the built-in heuristic score already
    stored in ``candidate.score``.

    Args:
        llm_client: An initialised OpenAI-compatible client (e.g.
            ``openai.OpenAI()``).  Must expose a
            ``chat.completions.create`` method.
        source_code: The original Python source being transpiled; used
            as context in the prompt.
        target_lang: Target language name (e.g. ``"javascript"``).
        model: The model identifier to use for completions.
            Defaults to ``"gpt-4o-mini"``.
    """

    def __init__(
        self,
        llm_client: Any,
        source_code: str,
        target_lang: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        self._client = llm_client
        self._source_code = source_code
        self._target_lang = target_lang
        self._model = model

    def __call__(self, candidate: "TranslationCandidate") -> float:
        """Score *candidate* using the LLM, falling back to heuristic.

        Args:
            candidate: The :class:`TranslationCandidate` to evaluate.

        Returns:
            A float score ∈ [0, 1].
        """
        prompt = _LLM_PROMPT_TEMPLATE.format(
            target_lang=self._target_lang,
            source_code=self._source_code,
            candidate_code=candidate.code_sketch,
        )
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=128,
            )
            content = response.choices[0].message.content or ""
            data = json.loads(content)
            score = float(data.get("score", candidate.score))
            return max(0.0, min(score, 1.0))
        except Exception as exc:  # noqa: BLE001
            _logger.debug("LLMScorer fallback (heuristic): %s", exc)
            return Inferir._heuristic_score(candidate)


def build_llm_scorer(
    source_code: str,
    target_lang: str,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
) -> Optional[LLMScorer]:
    """Convenience factory: create an :class:`LLMScorer` from env vars.

    Reads the ``OPENAI_API_KEY`` environment variable (or uses *api_key*
    if supplied) to initialise an ``openai.OpenAI`` client.

    Args:
        source_code: Original Python source being transpiled.
        target_lang: Target language name.
        model: LLM model identifier.
        api_key: Optional explicit API key.  Falls back to the
            ``OPENAI_API_KEY`` environment variable when *None*.

    Returns:
        An :class:`LLMScorer` if the ``openai`` package is installed and
        a key is available; otherwise *None* (caller should use heuristic).
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        _logger.debug("build_llm_scorer: no API key found; LLM disabled.")
        return None
    try:
        import openai  # noqa: E402  (lazy import — openai is optional at runtime)
        client = openai.OpenAI(api_key=key)
        return LLMScorer(client, source_code, target_lang, model=model)
    except ImportError:
        _logger.debug("build_llm_scorer: openai package not installed.")
        return None


# ---------------------------------------------------------------------------
# 𝕆  Operacionalizar — Mode 1
# ---------------------------------------------------------------------------

class Operacionalizar:
    """𝕆: Bring the algorithm into the real domain.

    Receives raw source code (string) and returns an EnrichedAST object —
    a Python ``ast.AST`` augmented with ontological and semantic metadata.
    This corresponds to the step of converting pseudocode or source text
    into an executable, inspectable artefact.

    Reference: §0.2 Mode 1 — Operacionalizar (𝕆).
    """

    def __call__(self, source_code: str) -> EnrichedAST:
        """Parse *source_code* and enrich its AST with metadata.

        Args:
            source_code: Python source code as a string.

        Returns:
            An :class:`EnrichedAST` containing the parsed tree and initial
            metadata (node type histogram, SHA-256 fingerprint, etc.).

        Raises:
            SyntaxError: If *source_code* is not valid Python.
        """
        tree = ast.parse(source_code)
        metadata = self._collect_metadata(tree, source_code)
        return EnrichedAST(tree=tree, metadata=metadata)

    # ------------------------------------------------------------------
    @staticmethod
    def _collect_metadata(tree: ast.AST, source_code: str) -> Dict[str, Any]:
        node_types: Dict[str, int] = {}
        for node in ast.walk(tree):
            key = type(node).__name__
            node_types[key] = node_types.get(key, 0) + 1

        sha = hashlib.sha256(source_code.encode()).hexdigest()
        return {
            "fingerprint": sha,
            "node_type_histogram": node_types,
            "total_nodes": sum(node_types.values()),
            "ontological_class": _infer_ontological_class(node_types),
            "semantic_domain": "generic",
        }


# ---------------------------------------------------------------------------
# ℙ  Processar — Mode 2
# ---------------------------------------------------------------------------

class Processar:
    """ℙ: Transform the algorithm step-by-step, modifying state.

    Receives an :class:`EnrichedAST` and produces an
    :class:`IntermediateState` — a symbolic digest of the algorithm's
    structure after traversal (analogous to code execution producing an
    intermediate representation).

    Reference: §0.2 Mode 2 — Processar (ℙ).
    """

    def __call__(self, enriched: EnrichedAST) -> IntermediateState:
        """Traverse *enriched* and produce a symbolic intermediate state.

        Args:
            enriched: The :class:`EnrichedAST` output from :class:`Operacionalizar`.

        Returns:
            An :class:`IntermediateState` capturing depth, node counts, and
            enriched metadata.
        """
        tree = enriched.tree
        depth = _tree_depth(tree)
        source_repr = ast.unparse(tree) if hasattr(ast, "unparse") else "<unparseable>"
        node_types = enriched.metadata.get("node_type_histogram", {})

        return IntermediateState(
            source_code=source_repr,
            node_count=enriched.metadata.get("total_nodes", 0),
            depth=depth,
            node_types=node_types,
            enriched_ast=enriched,
            metadata={**enriched.metadata, "processed": True, "tree_depth": depth},
        )


# ---------------------------------------------------------------------------
# 𝔻  Distribuir — Mode 3
# ---------------------------------------------------------------------------

class Distribuir:
    """𝔻: Spread the result of Processar across domains and nodes.

    Receives an :class:`IntermediateState` and returns a list of
    :class:`TranslationCandidate` objects — alternative representations
    of the algorithm in different target domains or languages.

    Reference: §0.2 Mode 3 — Distribuir (𝔻).
    """

    DEFAULT_TARGETS: Tuple[str, ...] = ("python", "javascript", "pseudocode")

    def __call__(
        self,
        state: IntermediateState,
        target_langs: Optional[List[str]] = None,
    ) -> List[TranslationCandidate]:
        """Generate candidate translations for *state*.

        Args:
            state: The :class:`IntermediateState` output from :class:`Processar`.
            target_langs: Languages to target; defaults to
                ``DEFAULT_TARGETS``.

        Returns:
            A list of :class:`TranslationCandidate` — one per target
            language.  Scores are initialised to 0.0 and refined later
            by :class:`Inferir`.
        """
        langs = target_langs or list(self.DEFAULT_TARGETS)
        candidates = []
        for lang in langs:
            sketch = self._sketch(state, lang)
            candidates.append(
                TranslationCandidate(
                    target_lang=lang,
                    code_sketch=sketch,
                    score=0.0,
                    metadata={"source_depth": state.depth},
                )
            )
        return candidates

    # ------------------------------------------------------------------
    @staticmethod
    def _sketch(state: IntermediateState, lang: str) -> str:
        """Produce a minimal structural sketch for *lang*."""
        header = {
            "python": "# Python translation sketch\n",
            "javascript": "// JavaScript translation sketch\n",
            "pseudocode": "-- Pseudocode sketch\n",
        }.get(lang, f"// {lang} translation sketch\n")
        return header + state.source_code


# ---------------------------------------------------------------------------
# 𝕀  Inferir — Mode 4
# ---------------------------------------------------------------------------

class Inferir:
    """𝕀: Derive implicit consequences from distributed candidates.

    Receives a list of :class:`TranslationCandidate` objects, applies
    heuristic scoring (or optionally delegates to an LLM via a pluggable
    *scorer*), and returns the single most significant candidate.

    Covers deduction, abduction, and induction as described in §0.2 Mode 4.

    Reference: §0.2 Mode 4 — Inferir (𝕀).
    """

    def __init__(self, scorer: Optional[Any] = None) -> None:
        """Initialise with an optional external scorer.

        Args:
            scorer: A callable ``scorer(candidate) -> float`` (e.g. an LLM
                    wrapper).  When *None*, a built-in heuristic is used.
        """
        self._scorer = scorer or self._heuristic_score

    def __call__(
        self, candidates: List[TranslationCandidate]
    ) -> TranslationCandidate:
        """Select the most significant candidate.

        Args:
            candidates: Output of :class:`Distribuir`.

        Returns:
            The :class:`TranslationCandidate` with the highest inferred
            significance score.

        Raises:
            ValueError: If *candidates* is empty.
        """
        if not candidates:
            raise ValueError("Inferir received an empty candidate list.")
        for c in candidates:
            c.score = float(self._scorer(c))
        return max(candidates, key=lambda c: c.score)

    # ------------------------------------------------------------------
    @staticmethod
    def _heuristic_score(candidate: TranslationCandidate) -> float:
        """Simple heuristic: longer, denser sketches are rewarded."""
        lines = candidate.code_sketch.splitlines()
        non_empty = sum(1 for ln in lines if ln.strip())
        unique_tokens = len(set(candidate.code_sketch.split()))
        raw = (non_empty * 0.5 + unique_tokens * 0.1) / 10.0
        return min(raw, 1.0)


# ---------------------------------------------------------------------------
# ℕ  Incidir — Mode 5
# ---------------------------------------------------------------------------

class Incidir:
    """ℕ: Project the chosen candidate into the world and compute f(A).

    Receives a :class:`TranslationCandidate`, generates the final artefact
    (the transpiled code string), and calculates the significance score
    f(A) ∈ ℝ≥0 that will feed the π-radical operator Π(A).

    This is the causal/incidental dimension: the artefact encounters its
    context and modifies it.

    Reference: §0.2 Mode 5 — Incidir (ℕ).
    """

    def __call__(
        self, candidate: TranslationCandidate
    ) -> Tuple[str, float]:
        """Materialise *candidate* and compute its significance score.

        Args:
            candidate: The winning :class:`TranslationCandidate` from
                :class:`Inferir`.

        Returns:
            A tuple ``(final_code, f_A)`` where *final_code* is the
            transpiled source string and *f_A* is the raw significance
            score before the π-radical is applied.
        """
        final_code = self._finalise(candidate)
        f_A = self._compute_significance(candidate, final_code)
        return final_code, f_A

    # ------------------------------------------------------------------
    @staticmethod
    def _finalise(candidate: TranslationCandidate) -> str:
        header = (
            f"# Target language: {candidate.target_lang}\n"
            f"# Significance score (pre-Π): {candidate.score:.4f}\n\n"
        )
        return header + candidate.code_sketch

    @staticmethod
    def _compute_significance(candidate: TranslationCandidate, code: str) -> float:
        """Aggregate structural and semantic features into f(A) ∈ (0, ∞)."""
        lines = code.splitlines()
        density = len([ln for ln in lines if ln.strip()]) / max(len(lines), 1)
        diversity = len(set(code.split())) / max(len(code.split()), 1)
        depth_bonus = math.log1p(candidate.metadata.get("source_depth", 1))
        f_A = (density * 0.4 + diversity * 0.4 + candidate.score * 0.2) * (1.0 + depth_bonus)
        return max(f_A, 1e-9)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _tree_depth(tree: ast.AST) -> int:
    """Return the maximum depth of an AST via iterative DFS."""
    stack = [(tree, 1)]
    max_depth = 0
    while stack:
        node, depth = stack.pop()
        max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(node):
            stack.append((child, depth + 1))
    return max_depth


def _infer_ontological_class(histogram: Dict[str, int]) -> str:
    """Infer a coarse ontological class from the AST node histogram."""
    if "ClassDef" in histogram:
        return "object-oriented"
    if "FunctionDef" in histogram or "AsyncFunctionDef" in histogram:
        return "procedural-functional"
    if "For" in histogram or "While" in histogram:
        return "iterative"
    return "declarative"
