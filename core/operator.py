"""
core/operator.py — The π-radical significance operator Π(A) = [f(A)]^(1/π).

Theoretical basis (§0.1 of the original work):
    The operator Π : Alg → ℝ≥0 is defined as
        Π(A) := [f(A)]^(1/π)  where π = 3.14159...

The key properties exploited here are:
    1. Irredutibility — the exponent 1/π is transcendental, so the result
       cannot be expressed in closed finite form for most f(A).
    2. Compression — it compresses peaks and raises minima relative to the
       identity, making structural significance relations legible.
    3. Convergence (Theorem 6.2) — iterating Π successively drives any
       positive finite value toward 1, because:
           lim_{n→∞} (f_A)^{(1/π)^n} = 1   for f_A > 0, f_A finite.
"""

import math
from typing import List


PI: float = math.pi
INV_PI: float = 1.0 / math.pi


def pi_radical_significance(f_A: float) -> float:
    """Compute the π-radical significance of a non-negative scalar f(A).

    Implements the canonical operator:
        Π(A) = [f(A)]^(1/π)

    Args:
        f_A: The significance score of algorithm A under evaluation
             function f.  Must be non-negative.

    Returns:
        The π-radical of f_A, a value in ℝ≥0.

    Raises:
        ValueError: If f_A is negative.
    """
    if f_A < 0:
        raise ValueError(f"f(A) must be non-negative; got {f_A}.")
    if f_A == 0:
        return 0.0
    return float(f_A ** INV_PI)


def iterate_convergence(f_A: float, n_iterations: int = 10) -> List[float]:
    """Demonstrate Theorem 6.2: iterative application of Π converges to 1.

    Each step applies the π-radical to the previous result:
        Π^(k)(A) = [Π^(k-1)(A)]^(1/π)

    For any positive finite f_A the sequence {Π^(k)(A)} → 1 as k → ∞,
    because the exponent accumulated is (1/π)^k → 0, and x^0 = 1 for
    all positive x.

    Args:
        f_A: The initial significance score f(A) > 0.
        n_iterations: Number of successive Π applications to compute.

    Returns:
        A list of length n_iterations + 1 containing
        [f_A, Π(f_A), Π²(f_A), ..., Π^n(f_A)].

    Raises:
        ValueError: If f_A is not positive.
    """
    if f_A <= 0:
        raise ValueError(f"f(A) must be strictly positive for convergence; got {f_A}.")
    trajectory: List[float] = [f_A]
    current = f_A
    for _ in range(n_iterations):
        current = pi_radical_significance(current)
        trajectory.append(current)
    return trajectory
