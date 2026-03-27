"""
ipii — Interação Paramétrica Iterativa por Interoperabilidade (IPII).

Implements the SemanticTranspiler that orchestrates the five operative modes
and evaluates transpilation quality using the six significance relations,
returning a π-radical significance score Π(A).
"""

from .transpiler import SemanticTranspiler
from .ast_parser import parse_and_enrich_ast

__all__ = ["SemanticTranspiler", "parse_and_enrich_ast"]
