"""
ipii/ast_parser.py — Enriched AST parser with ontological and semantic metadata.

Theoretical basis (§0.2 Mode 1 — Operacionalizar):
    The first operative mode (𝕆) converts a raw source-code string into
    an executable, inspectable artefact.  This module implements that
    conversion for Python source, adding ontological and semantic metadata
    to each node of the Abstract Syntax Tree.

Metadata attached per node:
    - ``_onto_class``: coarse ontological category (e.g. "function", "class")
    - ``_sem_domain``: inferred semantic domain (e.g. "arithmetic", "io")
    - ``_depth``: depth of the node within the tree
    - ``_node_id``: sequential integer identifier for graph traversal
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Metadata containers
# ---------------------------------------------------------------------------

@dataclass
class NodeMetadata:
    """Ontological and semantic annotations for a single AST node."""

    node_id: int
    node_type: str
    depth: int
    onto_class: str
    sem_domain: str
    children_ids: List[int] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnrichedModule:
    """A parsed Python module with a rich metadata registry."""

    tree: ast.AST
    source_fingerprint: str
    metadata_registry: Dict[int, NodeMetadata]  # keyed by NodeMetadata.node_id
    summary: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_and_enrich_ast(source_code: str) -> EnrichedModule:
    """Parse *source_code* and enrich every AST node with metadata.

    This function implements the 𝕆 (Operacionalizar) operative mode for
    Python source: it parses the source into a standard ``ast.AST`` and
    then walks the tree in depth-first order, annotating each node with:

    - An ontological class (function / class / control / expression / other)
    - A semantic domain (arithmetic / io / iteration / definition / generic)
    - Its depth within the tree
    - A unique sequential identifier (for graph-based downstream processing)

    The resulting :class:`EnrichedModule` carries both the original AST
    and a ``metadata_registry`` dictionary keyed by node id.

    Args:
        source_code: Valid Python 3 source code.

    Returns:
        An :class:`EnrichedModule` with tree + per-node metadata.

    Raises:
        SyntaxError: If *source_code* is not valid Python.
    """
    tree = ast.parse(source_code)
    fingerprint = hashlib.sha256(source_code.encode()).hexdigest()

    registry: Dict[int, NodeMetadata] = {}
    _counter = [0]  # mutable closure counter

    def _walk(node: ast.AST, depth: int, parent_id: Optional[int]) -> int:
        nid = _counter[0]
        _counter[0] += 1

        onto = _classify_ontological(node)
        sem = _classify_semantic(node)

        meta = NodeMetadata(
            node_id=nid,
            node_type=type(node).__name__,
            depth=depth,
            onto_class=onto,
            sem_domain=sem,
            children_ids=[],
        )

        # Attach lightweight attributes directly to the AST node
        node._meta_id = nid       # type: ignore[attr-defined]
        node._onto_class = onto   # type: ignore[attr-defined]
        node._sem_domain = sem    # type: ignore[attr-defined]
        node._depth = depth       # type: ignore[attr-defined]

        registry[nid] = meta

        if parent_id is not None and parent_id in registry:
            registry[parent_id].children_ids.append(nid)

        for child in ast.iter_child_nodes(node):
            _walk(child, depth + 1, nid)

        return nid

    _walk(tree, depth=0, parent_id=None)

    summary = _build_summary(registry, source_code)
    return EnrichedModule(
        tree=tree,
        source_fingerprint=fingerprint,
        metadata_registry=registry,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_ONTO_FUNCTION_NODES = frozenset({"FunctionDef", "AsyncFunctionDef", "Lambda"})
_ONTO_CLASS_NODES = frozenset({"ClassDef"})
_ONTO_CONTROL_NODES = frozenset({
    "If", "For", "While", "AsyncFor", "With", "AsyncWith",
    "Try", "ExceptHandler", "Assert", "Break", "Continue", "Return",
})


def _classify_ontological(node: ast.AST) -> str:
    """Assign a coarse ontological class to *node*."""
    name = type(node).__name__
    if name in _ONTO_FUNCTION_NODES:
        return "function"
    if name in _ONTO_CLASS_NODES:
        return "class"
    if name in _ONTO_CONTROL_NODES:
        return "control"
    if name in ("Expr", "Call", "BinOp", "UnaryOp", "BoolOp", "Compare"):
        return "expression"
    if name in ("Assign", "AugAssign", "AnnAssign"):
        return "assignment"
    if name in ("Import", "ImportFrom"):
        return "import"
    if name in ("Module",):
        return "module"
    return "other"


_SEM_ARITHMETIC = frozenset({
    "BinOp", "UnaryOp", "Add", "Sub", "Mult", "Div",
    "Mod", "Pow", "FloorDiv", "MatMult",
})
_SEM_IO = frozenset({"Print", "Input"})  # pseudo-nodes for illustration
_SEM_ITER = frozenset({"For", "While", "AsyncFor", "GeneratorExp", "ListComp"})
_SEM_DEF = frozenset({"FunctionDef", "AsyncFunctionDef", "ClassDef", "Lambda"})


def _classify_semantic(node: ast.AST) -> str:
    """Assign a coarse semantic domain to *node*."""
    name = type(node).__name__
    if name in _SEM_ARITHMETIC:
        return "arithmetic"
    if name in _SEM_IO:
        return "io"
    if name in _SEM_ITER:
        return "iteration"
    if name in _SEM_DEF:
        return "definition"
    # Heuristic for function calls to known IO built-ins
    if name == "Call" and isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in ("print", "input", "open"):
            return "io"
    return "generic"


def _build_summary(
    registry: Dict[int, NodeMetadata], source_code: str
) -> Dict[str, Any]:
    """Produce a high-level summary of the enriched module."""
    onto_counts: Dict[str, int] = {}
    sem_counts: Dict[str, int] = {}
    max_depth = 0

    for meta in registry.values():
        onto_counts[meta.onto_class] = onto_counts.get(meta.onto_class, 0) + 1
        sem_counts[meta.sem_domain] = sem_counts.get(meta.sem_domain, 0) + 1
        max_depth = max(max_depth, meta.depth)

    return {
        "total_nodes": len(registry),
        "max_depth": max_depth,
        "ontological_distribution": onto_counts,
        "semantic_distribution": sem_counts,
        "source_line_count": source_code.count("\n") + 1,
    }
