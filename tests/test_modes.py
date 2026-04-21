"""
tests/test_modes.py — Tests for the five operative modes in core/modes.py.

Covers:
    𝕆  Operacionalizar — parse + enrich
    ℙ  Processar       — intermediate state
    𝔻  Distribuir      — candidate generation (incl. real codegen)
    𝕀  Inferir         — candidate selection
    ℕ  Incidir         — materialisation + significance score
    Integration        — full pipeline O→P→D→I→N
"""

import sys
import os
import math

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.modes import (
    Operacionalizar,
    Processar,
    Distribuir,
    Inferir,
    Incidir,
    EnrichedAST,
    IntermediateState,
    TranslationCandidate,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_SIMPLE_SOURCE = "x = 1"
_FUNC_SOURCE = "def add(a, b):\n    return a + b"
_CLASS_SOURCE = "class Foo:\n    def bar(self):\n        return 42"


# ---------------------------------------------------------------------------
# 𝕆  Operacionalizar
# ---------------------------------------------------------------------------

class TestOperacionalizar:
    def test_returns_enriched_ast(self) -> None:
        O = Operacionalizar()
        result = O(_SIMPLE_SOURCE)
        assert isinstance(result, EnrichedAST)

    def test_metadata_contains_fingerprint(self) -> None:
        O = Operacionalizar()
        result = O(_SIMPLE_SOURCE)
        assert "fingerprint" in result.metadata
        assert len(result.metadata["fingerprint"]) == 64  # SHA-256 hex

    def test_metadata_node_histogram(self) -> None:
        O = Operacionalizar()
        result = O(_FUNC_SOURCE)
        hist = result.metadata["node_type_histogram"]
        assert "FunctionDef" in hist

    def test_metadata_total_nodes(self) -> None:
        O = Operacionalizar()
        result = O(_SIMPLE_SOURCE)
        assert result.metadata["total_nodes"] > 0

    def test_ontological_class_procedural(self) -> None:
        O = Operacionalizar()
        result = O(_FUNC_SOURCE)
        assert result.metadata["ontological_class"] == "procedural-functional"

    def test_ontological_class_oo(self) -> None:
        O = Operacionalizar()
        result = O(_CLASS_SOURCE)
        assert result.metadata["ontological_class"] == "object-oriented"

    def test_invalid_python_raises_syntax_error(self) -> None:
        O = Operacionalizar()
        with pytest.raises(SyntaxError):
            O("def (:")

    def test_same_source_same_fingerprint(self) -> None:
        O = Operacionalizar()
        r1 = O(_SIMPLE_SOURCE)
        r2 = O(_SIMPLE_SOURCE)
        assert r1.metadata["fingerprint"] == r2.metadata["fingerprint"]

    def test_different_source_different_fingerprint(self) -> None:
        O = Operacionalizar()
        r1 = O(_SIMPLE_SOURCE)
        r2 = O(_FUNC_SOURCE)
        assert r1.metadata["fingerprint"] != r2.metadata["fingerprint"]


# ---------------------------------------------------------------------------
# ℙ  Processar
# ---------------------------------------------------------------------------

class TestProcessar:
    def test_returns_intermediate_state(self) -> None:
        O, P = Operacionalizar(), Processar()
        result = P(O(_FUNC_SOURCE))
        assert isinstance(result, IntermediateState)

    def test_depth_greater_than_zero(self) -> None:
        O, P = Operacionalizar(), Processar()
        state = P(O(_FUNC_SOURCE))
        assert state.depth > 0

    def test_node_count_positive(self) -> None:
        O, P = Operacionalizar(), Processar()
        state = P(O(_FUNC_SOURCE))
        assert state.node_count > 0

    def test_source_code_is_string(self) -> None:
        O, P = Operacionalizar(), Processar()
        state = P(O(_FUNC_SOURCE))
        assert isinstance(state.source_code, str)

    def test_metadata_processed_flag(self) -> None:
        O, P = Operacionalizar(), Processar()
        state = P(O(_SIMPLE_SOURCE))
        assert state.metadata.get("processed") is True

    def test_deeper_code_has_greater_depth(self) -> None:
        O, P = Operacionalizar(), Processar()
        shallow = P(O(_SIMPLE_SOURCE))
        deep = P(O(_CLASS_SOURCE))
        assert deep.depth >= shallow.depth


# ---------------------------------------------------------------------------
# 𝔻  Distribuir
# ---------------------------------------------------------------------------

class TestDistribuir:
    def test_default_targets_produces_four_candidates(self) -> None:
        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_FUNC_SOURCE))
        candidates = D(state)
        assert len(candidates) == 4  # python, javascript, rust, pseudocode

    def test_custom_targets(self) -> None:
        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_SIMPLE_SOURCE))
        candidates = D(state, target_langs=["javascript", "rust"])
        assert len(candidates) == 2
        langs = {c.target_lang for c in candidates}
        assert langs == {"javascript", "rust"}

    def test_javascript_candidate_uses_codegen(self) -> None:
        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_FUNC_SOURCE))
        candidates = D(state, target_langs=["javascript"])
        js = candidates[0].code_sketch
        # Real codegen emits `function` keyword
        assert "function add(a, b)" in js

    def test_rust_candidate_uses_codegen(self) -> None:
        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_FUNC_SOURCE))
        candidates = D(state, target_langs=["rust"])
        rs = candidates[0].code_sketch
        assert "fn add(" in rs

    def test_python_candidate_is_source(self) -> None:
        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_SIMPLE_SOURCE))
        candidates = D(state, target_langs=["python"])
        py = candidates[0].code_sketch
        assert "x = 1" in py

    def test_candidate_scores_initialised_to_zero(self) -> None:
        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_SIMPLE_SOURCE))
        for c in D(state):
            assert c.score == 0.0

    def test_candidate_metadata_depth(self) -> None:
        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_SIMPLE_SOURCE))
        for c in D(state):
            assert "source_depth" in c.metadata


# ---------------------------------------------------------------------------
# 𝕀  Inferir
# ---------------------------------------------------------------------------

class TestInferir:
    def test_returns_translation_candidate(self) -> None:
        O, P, D, I = Operacionalizar(), Processar(), Distribuir(), Inferir()
        state = P(O(_FUNC_SOURCE))
        best = I(D(state))
        assert isinstance(best, TranslationCandidate)

    def test_best_has_highest_score(self) -> None:
        O, P, D, I = Operacionalizar(), Processar(), Distribuir(), Inferir()
        state = P(O(_FUNC_SOURCE))
        candidates = D(state)
        best = I(candidates)
        assert all(best.score >= c.score for c in candidates)

    def test_empty_candidates_raises(self) -> None:
        I = Inferir()
        with pytest.raises(ValueError, match="empty"):
            I([])

    def test_custom_scorer_is_called(self) -> None:
        called = []

        def my_scorer(c: TranslationCandidate) -> float:
            called.append(c.target_lang)
            return 0.5

        O, P, D = Operacionalizar(), Processar(), Distribuir()
        state = P(O(_SIMPLE_SOURCE))
        candidates = D(state, target_langs=["javascript", "rust"])
        I = Inferir(scorer=my_scorer)
        I(candidates)
        assert len(called) == 2

    def test_score_in_range(self) -> None:
        O, P, D, I = Operacionalizar(), Processar(), Distribuir(), Inferir()
        state = P(O(_CLASS_SOURCE))
        best = I(D(state))
        assert 0.0 <= best.score <= 1.0


# ---------------------------------------------------------------------------
# ℕ  Incidir
# ---------------------------------------------------------------------------

class TestIncidir:
    def test_returns_tuple(self) -> None:
        O, P, D, I, N = (
            Operacionalizar(), Processar(), Distribuir(), Inferir(), Incidir()
        )
        state = P(O(_FUNC_SOURCE))
        result = N(I(D(state)))
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_final_code_is_string(self) -> None:
        O, P, D, I, N = (
            Operacionalizar(), Processar(), Distribuir(), Inferir(), Incidir()
        )
        state = P(O(_FUNC_SOURCE))
        final_code, _ = N(I(D(state)))
        assert isinstance(final_code, str)

    def test_significance_is_positive(self) -> None:
        O, P, D, I, N = (
            Operacionalizar(), Processar(), Distribuir(), Inferir(), Incidir()
        )
        state = P(O(_FUNC_SOURCE))
        _, f_A = N(I(D(state)))
        assert f_A > 0.0
        assert math.isfinite(f_A)

    def test_final_code_contains_target_lang(self) -> None:
        O, P, D, I, N = (
            Operacionalizar(), Processar(), Distribuir(), Inferir(), Incidir()
        )
        state = P(O(_FUNC_SOURCE))
        final_code, _ = N(I(D(state)))
        assert "Target language:" in final_code


# ---------------------------------------------------------------------------
# Integration: full pipeline
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    def test_full_pipeline_simple(self) -> None:
        O, P, D, I, N = (
            Operacionalizar(), Processar(), Distribuir(), Inferir(), Incidir()
        )
        final_code, f_A = N(I(D(P(O(_SIMPLE_SOURCE)))))
        assert isinstance(final_code, str)
        assert f_A > 0.0

    def test_full_pipeline_function(self) -> None:
        O, P, D, I, N = (
            Operacionalizar(), Processar(), Distribuir(), Inferir(), Incidir()
        )
        final_code, f_A = N(I(D(P(O(_FUNC_SOURCE)))))
        assert "function" in final_code or "fn " in final_code

    def test_full_pipeline_class(self) -> None:
        O, P, D, I, N = (
            Operacionalizar(), Processar(), Distribuir(), Inferir(), Incidir()
        )
        final_code, f_A = N(I(D(P(O(_CLASS_SOURCE)))))
        assert isinstance(final_code, str)
        assert math.isfinite(f_A)
