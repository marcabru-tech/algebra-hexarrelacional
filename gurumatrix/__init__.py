"""
gurumatrix — The 5-dimensional significance tensor G(i,j,k,t,l).

The GuruMatrix catalogues computational patterns across five ontological
dimensions: Ontological Category, Semantic Field, Hermeneutic Level,
Execution Time, and Target Language.
"""

from .tensor import GuruMatrix, OntologicalCategory, SemanticField, HermeneuticLevel

__all__ = ["GuruMatrix", "OntologicalCategory", "SemanticField", "HermeneuticLevel"]
