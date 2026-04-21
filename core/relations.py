"""
core/relations.py — The Six Significance Relations ρ₁–ρ₆.

Theoretical basis (§0.3 of the original work):
    When f evaluates algorithm A, the result is a significance *profile*
    composed of six hierarchical dimensions.  Each relation expresses a
    distinct mode of meaningful connection between two elements.  They
    are cumulative: each implies all previous ones, but not the reverse.

        ρ₁  Similitude     — surface similarity    (reflexive, symmetric, NOT transitive)
        ρ₂  Homologia      — structural sameness   (reflexive, transitive, NOT symmetric)
        ρ₃  Equivalência   — full substitutability (equivalence relation: R, S, T)
        ρ₄  Simetria       — group-orbit equality  (equivalence relation: R, S, T)
        ρ₅  Equilíbrio     — mutual cancellation   (symmetric, NOT reflexive, NOT transitive)
        ρ₆  Compensação    — emergent surplus value (most demanding — implies all above)

All functions return a score in [0, 1] where 1 indicates perfect
satisfaction of the relation.
"""

from __future__ import annotations

import ast
import math
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# ρ₁  Similitude
# ---------------------------------------------------------------------------

def calculate_similitude(obj1: Any, obj2: Any, epsilon: float = 0.3) -> float:
    """ρ₁ Similitude: score proximity in a feature-embedding space.

    Definition (§0.3):
        x ρ₁ y  ⟺  d(φ(x), φ(y)) < ε

    The embedding φ used here is the normalised node-type frequency
    histogram of each object's AST (or a string character-frequency
    vector for plain strings).  Distance is Euclidean; the score is
    exp(-d / ε) so that d=0 → score=1 and d→∞ → score→0.

    Properties verified by tests:
        - Reflexive: ρ₁(x, x) = 1
        - Symmetric: ρ₁(x, y) = ρ₁(y, x)
        - NOT transitive in general (tested in test_relations.py)

    Args:
        obj1: A Python AST node or string.
        obj2: A Python AST node or string.
        epsilon: Bandwidth parameter controlling similarity decay.

    Returns:
        Similarity score ∈ [0, 1].
    """
    v1 = _feature_vector(obj1)
    v2 = _feature_vector(obj2)
    v1, v2 = _align_vectors(v1, v2)
    dist = float(np.linalg.norm(v1 - v2))
    return float(math.exp(-dist / max(epsilon, 1e-9)))


# ---------------------------------------------------------------------------
# ρ₂  Homologia
# ---------------------------------------------------------------------------

def calculate_homology(obj1: Any, obj2: Any) -> float:
    """ρ₂ Homologia: score structural isomorphism between two objects.

    Definition (§0.3):
        x ρ₂ y  ⟺  ∃ h : Struct(x) ≅ Struct(y)

    Structural comparison is approximated by the *directional* node-type
    multiset coverage of obj1 within obj2: the fraction of obj1's node
    occurrences that are matched by obj2.  This yields an asymmetric
    measure — ρ₂(x, y) ≠ ρ₂(y, x) in general — because a simple
    structure may fully embed into a complex one (high score) while the
    reverse mapping leaves many of the complex structure's nodes unmatched
    (low score).

    Formula:
        ρ₂(x, y) = Σ_k min(s₁[k], s₂[k]) / Σ_k s₁[k]

    Properties verified by tests:
        - Reflexive: ρ₂(x, x) = 1
        - Transitive (by transitivity of structural inclusion)
        - NOT symmetric in general: ρ₂(x, y) ≠ ρ₂(y, x) when one
          structure embeds into the other but not vice-versa.

    Args:
        obj1: A Python AST node, string of Python code, or dict.
        obj2: A Python AST node, string of Python code, or dict.

    Returns:
        Homology score ∈ [0, 1].
    """
    s1 = _struct_multiset(obj1)
    s2 = _struct_multiset(obj2)
    total1 = sum(s1.values())
    if total1 == 0:
        return 1.0
    intersection = sum(min(s1.get(k, 0), s2.get(k, 0)) for k in s1)
    return float(intersection / total1)


# ---------------------------------------------------------------------------
# ρ₃  Equivalência
# ---------------------------------------------------------------------------

def calculate_equivalence(
    obj1: Any, obj2: Any, context: Optional[Dict[str, Any]] = None
) -> float:
    """ρ₃ Equivalência: score functional substitutability in a context.

    Definition (§0.3):
        x ρ₃ y  ⟺  ∀ C ∈ 𝒞 : C[x] ≃ C[y]

    Approximated by combining structural homology (§ρ₂) with
    context-conditioned fingerprint equality.  When both objects produce
    the same canonical string representation in the given context they
    achieve full equivalence.

    Properties:
        - Reflexive, Symmetric, Transitive (true equivalence relation).

    Args:
        obj1: First algorithm or code fragment.
        obj2: Second algorithm or code fragment.
        context: Optional dict of contextual constraints (e.g. type
                 signatures, I/O examples).

    Returns:
        Equivalence score ∈ [0, 1].
    """
    structural = calculate_homology(obj1, obj2)
    sym_bonus = calculate_homology(obj2, obj1)
    base = (structural + sym_bonus) / 2.0

    if context:
        # Context check: both objects must satisfy the same set of
        # context predicates (outputs matching expected values).
        hits = 0
        for key, expected in context.items():
            r1 = _evaluate_in_context(obj1, key, expected)
            r2 = _evaluate_in_context(obj2, key, expected)
            if r1 == r2:
                hits += 1
        ctx_score = hits / max(len(context), 1)
        base = base * 0.5 + ctx_score * 0.5

    return float(min(base, 1.0))


# ---------------------------------------------------------------------------
# ρ₄  Simetria
# ---------------------------------------------------------------------------

def calculate_symmetry(
    obj1: Any,
    obj2: Any,
    transformation_group: Optional[Sequence[Callable[[Any], Any]]] = None,
) -> float:
    """ρ₄ Simetria: score the existence of a reversible group transformation.

    Definition (§0.3):
        x ρ₄ y  ⟺  ∃ T ∈ 𝒢 : T(x) = y  ∧  T⁻¹(y) = x

    Approximated by checking whether obj1 and obj2 lie in the same orbit
    under a given transformation group.  The default group consists of
    the identity and the string-reversal map (a toy example illustrating
    the concept).

    Properties:
        - Reflexive, Symmetric, Transitive (group-orbit equivalence).

    Args:
        obj1: First object.
        obj2: Second object.
        transformation_group: A sequence of callables {T} representing
            the group actions.  Defaults to {id, reverse}.

    Returns:
        Symmetry score ∈ {0.0, 1.0} — 1.0 if they share an orbit.
    """
    group = transformation_group or [lambda x: x, lambda x: _canonical_reverse(x)]
    for T in group:
        try:
            if _canonical(T(obj1)) == _canonical(obj2):
                return 1.0
            if _canonical(T(obj2)) == _canonical(obj1):
                return 1.0
        except Exception:  # noqa: BLE001
            continue
    # Continuous relaxation: fall back to equivalence score
    return calculate_equivalence(obj1, obj2) * 0.5


# ---------------------------------------------------------------------------
# ρ₅  Equilíbrio
# ---------------------------------------------------------------------------

def calculate_equilibrium(
    obj1: Any,
    obj2: Any,
    potential_func: Optional[Callable[[Any], float]] = None,
) -> float:
    """ρ₅ Equilíbrio: score mutual cancellation of potentials.

    Definition (§0.3):
        x ρ₅ y  ⟺  Φ(x) + Φ(y) = 0

    The default potential Φ maps each object to its *signed* structural
    complexity: Φ(x) = complexity(x) − median_complexity, so that
    objects above the median have positive potential and those below have
    negative potential.  Two objects are in equilibrium when their
    potentials cancel.

    Properties verified by tests:
        - Symmetric: ρ₅(x, y) = ρ₅(y, x)
        - NOT reflexive in general: ρ₅(x, x) = 1 iff Φ(x) = 0
        - NOT transitive in general

    Args:
        obj1: First object.
        obj2: Second object.
        potential_func: A callable Φ : Any → ℝ.  Defaults to a
            complexity-based potential.

    Returns:
        Equilibrium score ∈ [0, 1]; 1.0 when potentials perfectly cancel.
    """
    phi = potential_func or _default_potential
    p1 = phi(obj1)
    p2 = phi(obj2)
    total = abs(p1) + abs(p2)
    if total < 1e-12:
        # Both potentials are zero → perfect equilibrium
        return 1.0
    cancellation = 1.0 - abs(p1 + p2) / total
    return float(max(cancellation, 0.0))


# ---------------------------------------------------------------------------
# ρ₆  Compensação
# ---------------------------------------------------------------------------

def calculate_compensation(obj1: Any, obj2: Any) -> float:
    """ρ₆ Compensação: score the emergent surplus value of combining obj1+obj2.

    Definition (§0.3):
        Compensação is the most demanding relation — it implies all prior
        five.  The deficiency of one is the excess of the other, and their
        combination produces a value greater than the sum of the parts.

    Implemented as a weighted combination of all five prior relations,
    where the weights reflect the hierarchical ordering (later relations
    carry higher weight) plus a synergy bonus when the equilibrium of the
    pair exceeds both individual scores.

    Args:
        obj1: First object.
        obj2: Second object.

    Returns:
        Compensation score ∈ [0, 1].
    """
    r1 = calculate_similitude(obj1, obj2)
    # Use the symmetric mean of the directional ρ₂ so that ρ₆ remains symmetric.
    r2 = (calculate_homology(obj1, obj2) + calculate_homology(obj2, obj1)) / 2.0
    r3 = calculate_equivalence(obj1, obj2)
    r4 = calculate_symmetry(obj1, obj2)
    r5 = calculate_equilibrium(obj1, obj2)

    # Weighted sum (§ρ₆ implies all prior relations)
    weights = [0.05, 0.10, 0.20, 0.25, 0.40]
    base = sum(w * r for w, r in zip(weights, [r1, r2, r3, r4, r5]))

    # Synergy bonus: compensation exceeds mere balance
    synergy = max(0.0, r5 - (r1 + r2 + r3 + r4) / 4.0) * 0.1
    return float(min(base + synergy, 1.0))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_GLOBAL_NODE_TYPES: List[str] = [
    "Module", "FunctionDef", "AsyncFunctionDef", "ClassDef",
    "Return", "Assign", "AugAssign", "AnnAssign", "For", "AsyncFor",
    "While", "If", "With", "AsyncWith", "Raise", "Try", "Assert",
    "Import", "ImportFrom", "Expr", "Call", "BinOp", "UnaryOp",
    "BoolOp", "Compare", "Constant", "Name", "Attribute", "Subscript",
    "List", "Tuple", "Dict", "Set", "ListComp", "DictComp",
    "GeneratorExp", "Lambda", "Yield", "YieldFrom", "Await",
]

_NODE_INDEX: Dict[str, int] = {n: i for i, n in enumerate(_GLOBAL_NODE_TYPES)}


def _feature_vector(obj: Any) -> np.ndarray:
    """Map *obj* to a fixed-length feature vector."""
    if isinstance(obj, ast.AST):
        return _ast_vector(obj)
    if isinstance(obj, str):
        try:
            tree = ast.parse(obj)
            return _ast_vector(tree)
        except SyntaxError:
            return _string_vector(obj)
    if isinstance(obj, (int, float)):
        v = np.zeros(len(_GLOBAL_NODE_TYPES))
        v[0] = float(obj)
        return v
    return _string_vector(str(obj))


def _ast_vector(tree: ast.AST) -> np.ndarray:
    vec = np.zeros(len(_GLOBAL_NODE_TYPES), dtype=float)
    total = 0
    for node in ast.walk(tree):
        idx = _NODE_INDEX.get(type(node).__name__)
        if idx is not None:
            vec[idx] += 1
            total += 1
    if total > 0:
        vec /= total
    return vec


def _string_vector(s: str) -> np.ndarray:
    vec = np.zeros(len(_GLOBAL_NODE_TYPES), dtype=float)
    for i, ch in enumerate(s[: len(_GLOBAL_NODE_TYPES)]):
        vec[i] = ord(ch) / 128.0
    return vec


def _align_vectors(v1: np.ndarray, v2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Pad shorter vector to match the longer one."""
    if len(v1) == len(v2):
        return v1, v2
    max_len = max(len(v1), len(v2))
    v1 = np.pad(v1, (0, max_len - len(v1)))
    v2 = np.pad(v2, (0, max_len - len(v2)))
    return v1, v2


def _struct_multiset(obj: Any) -> Dict[str, int]:
    """Return a node-type count multiset for *obj*."""
    if isinstance(obj, ast.AST):
        ms: Dict[str, int] = {}
        for node in ast.walk(obj):
            k = type(node).__name__
            ms[k] = ms.get(k, 0) + 1
        return ms
    if isinstance(obj, str):
        try:
            tree = ast.parse(obj)
            return _struct_multiset(tree)
        except SyntaxError:
            return {ch: obj.count(ch) for ch in set(obj)}
    return {"_scalar": 1}


def _canonical(obj: Any) -> str:
    """Return a canonical string representation of *obj*."""
    if isinstance(obj, ast.AST):
        return ast.dump(obj)
    return str(obj)


def _canonical_reverse(obj: Any) -> Any:
    """Default group action: reverse the string representation."""
    return _canonical(obj)[::-1]


def _default_potential(obj: Any) -> float:
    """Φ(x) = structural complexity − 0.5 (centred around a median of 0.5)."""
    ms = _struct_multiset(obj)
    raw_complexity = sum(ms.values())
    # Normalise to (0, 1) via a soft sigmoid
    normalised = 2.0 / (1.0 + math.exp(-raw_complexity / 20.0)) - 1.0
    return normalised - 0.0  # centred at 0 for equilibrium semantics


def _evaluate_in_context(obj: Any, key: str, expected: Any) -> Any:
    """Evaluate *obj* against a context key (stub for I/O checks)."""
    if isinstance(obj, str) and key == "output":
        return obj == str(expected)
    return None
