"""
examples/semantic_transpilation.py — End-to-end IPII demo.

This script showcases the Álgebra Hexarrelacional de Significância in
action:

    1.  We define a simple Python algorithm (a recursive factorial).
    2.  The SemanticTranspiler orchestrates the five operative modes
        (𝕆 → ℙ → 𝔻 → 𝕀 → ℕ) in an iterative IPII loop.
    3.  The GuruMatrix reports the significance-space distance between
        Python and the target language.
    4.  The π-radical operator Π(A) = [f(A)]^(1/π) is applied, and all
        six significance relation scores are displayed.

Usage::

    python examples/semantic_transpilation.py

Or with a custom target language::

    python examples/semantic_transpilation.py --target rust
"""

from __future__ import annotations

import sys
import os
import math

# Allow running from the repository root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from ipii.transpiler import SemanticTranspiler
from ipii.ast_parser import parse_and_enrich_ast
from gurumatrix.tensor import GuruMatrix, TargetLanguage
from core.operator import iterate_convergence


# ---------------------------------------------------------------------------
# Sample algorithm
# ---------------------------------------------------------------------------

SAMPLE_SOURCE = '''\
def factorial(n: int) -> int:
    """Return n! using tail-recursive style."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def fibonacci(n: int) -> int:
    """Return the n-th Fibonacci number."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
'''


def _target_lang_index(name: str) -> TargetLanguage:
    mapping = {
        "python": TargetLanguage.PYTHON,
        "javascript": TargetLanguage.JAVASCRIPT,
        "typescript": TargetLanguage.TYPESCRIPT,
        "rust": TargetLanguage.RUST,
        "pseudocode": TargetLanguage.PSEUDOCODE,
    }
    return mapping.get(name.lower(), TargetLanguage.JAVASCRIPT)


def main(target: str = "javascript") -> None:
    console = Console() if HAS_RICH else None

    def _print(msg: str = "", **kwargs: object) -> None:
        if console:
            console.print(msg, **kwargs)
        else:
            print(msg)

    _print(
        "[bold cyan]π√f(A) — Álgebra Hexarrelacional de Significância[/bold cyan]"
        if HAS_RICH else "π√f(A) — Álgebra Hexarrelacional de Significância"
    )
    _print()

    # ── Step 1: Enrich the AST ──────────────────────────────────────────────
    _print("[bold]Step 1[/bold] — Operacionalizar: parsing & enriching AST …"
           if HAS_RICH else "Step 1 — Operacionalizar: parsing & enriching AST …")
    enriched_module = parse_and_enrich_ast(SAMPLE_SOURCE)
    summary = enriched_module.summary
    _print(f"  Total nodes : {summary['total_nodes']}")
    _print(f"  Max depth   : {summary['max_depth']}")
    _print(f"  Ontological : {summary['ontological_distribution']}")
    _print(f"  Semantic    : {summary['semantic_distribution']}")
    _print()

    # ── Step 2: GuruMatrix language distance ────────────────────────────────
    _print("[bold]Step 2[/bold] — GuruMatrix: computing language distance …"
           if HAS_RICH else "Step 2 — GuruMatrix: computing language distance …")
    gm = GuruMatrix()
    src_lang_idx = TargetLanguage.PYTHON
    tgt_lang_idx = _target_lang_index(target)
    dist = gm.calculate_language_distance(src_lang_idx, tgt_lang_idx)
    _print(f"  Distance (Python → {target}): {dist:.6f}")
    _print()

    # ── Step 3: IPII transpilation ──────────────────────────────────────────
    _print(f"[bold]Step 3[/bold] — IPII: transpiling Python → {target} …"
           if HAS_RICH else f"Step 3 — IPII: transpiling Python → {target} …")
    transpiler = SemanticTranspiler(max_iterations=8, tolerance=1e-5)
    result = transpiler.transpile(SAMPLE_SOURCE, target_lang=target)
    _print(f"  Iterations  : {result.iterations}")
    _print(f"  f(A)        : {result.f_A:.6f}")
    _print(f"  Π(A)        : {result.pi_A:.6f}  [= f(A)^(1/π)]")
    _print()

    # ── Step 4: Relation profile table ─────────────────────────────────────
    _print("[bold]Step 4[/bold] — Six significance relations profile:"
           if HAS_RICH else "Step 4 — Six significance relations profile:")
    if HAS_RICH and console:
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
        table.add_column("Relation", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Interpretation")
        rows = [
            ("ρ₁ Similitude",   "rho1_similitude",   "Surface similarity of embeddings"),
            ("ρ₂ Homologia",    "rho2_homology",      "Structural isomorphism of ASTs"),
            ("ρ₃ Equivalência", "rho3_equivalence",   "Functional substitutability"),
            ("ρ₄ Simetria",     "rho4_symmetry",      "Group-reversible transformation"),
            ("ρ₅ Equilíbrio",   "rho5_equilibrium",   "Mutual potential cancellation"),
            ("ρ₆ Compensação",  "rho6_compensation",  "Emergent surplus value"),
        ]
        for label, key, interp in rows:
            score = result.relation_scores.get(key, 0.0)
            table.add_row(label, f"{score:.4f}", interp)
        console.print(table)
    else:
        for key, val in result.relation_scores.items():
            print(f"  {key}: {val:.4f}")
    _print()

    # ── Step 5: Convergence trajectory ─────────────────────────────────────
    _print("[bold]Step 5[/bold] — Convergence trajectory of Π^(n)(A):"
           if HAS_RICH else "Step 5 — Convergence trajectory of Π^(n)(A):")
    trajectory = iterate_convergence(result.f_A, n_iterations=8)
    for i, val in enumerate(trajectory):
        _print(f"  Π^{i}(A) = {val:.8f}")
    _print()

    # ── Step 6: Generated code preview ─────────────────────────────────────
    _print("[bold]Step 6[/bold] — Generated transpilation (preview):"
           if HAS_RICH else "Step 6 — Generated transpilation (preview):")
    preview_lines = result.final_code.splitlines()[:20]
    preview = "\n".join(preview_lines)
    if HAS_RICH and console:
        console.print(Panel(preview, title=f"[{target}]", expand=False))
    else:
        print(preview)


if __name__ == "__main__":
    target_lang = "javascript"
    if len(sys.argv) >= 3 and sys.argv[1] == "--target":
        target_lang = sys.argv[2]
    elif len(sys.argv) == 2:
        target_lang = sys.argv[1]
    main(target=target_lang)
