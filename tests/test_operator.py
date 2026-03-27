"""
tests/test_operator.py — Mathematical proofs for the π-radical operator.

Tests:
    1. Basic computation of Π(A) = f_A^(1/π)
    2. Theorem 6.2: iterative convergence to 1 for any positive f_A
    3. Boundary conditions (f_A = 0, f_A = 1, f_A → ∞)
    4. Monotonicity: f_A₁ < f_A₂  ⟹  Π(f_A₁) < Π(f_A₂)
"""

import math
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.operator import pi_radical_significance, iterate_convergence, PI, INV_PI


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------

class TestPiRadicalSignificance:
    def test_zero_returns_zero(self) -> None:
        assert pi_radical_significance(0.0) == 0.0

    def test_one_returns_one(self) -> None:
        result = pi_radical_significance(1.0)
        assert math.isclose(result, 1.0, rel_tol=1e-12), f"Expected 1.0, got {result}"

    def test_known_value(self) -> None:
        # 2^(1/π) ≈ 1.24915...
        expected = 2.0 ** INV_PI
        result = pi_radical_significance(2.0)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_large_value(self) -> None:
        # Should not overflow — large f_A is compressed toward a finite value
        result = pi_radical_significance(1e6)
        assert result > 1.0
        assert math.isfinite(result)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            pi_radical_significance(-1.0)

    def test_returns_float(self) -> None:
        result = pi_radical_significance(4.0)
        assert isinstance(result, float)

    def test_monotonicity(self) -> None:
        """Π is monotone increasing: f_A₁ < f_A₂ ⟹ Π(f_A₁) < Π(f_A₂)."""
        values = [0.1, 0.5, 1.0, 2.0, 10.0, 100.0]
        pi_values = [pi_radical_significance(v) for v in values]
        for i in range(len(pi_values) - 1):
            assert pi_values[i] < pi_values[i + 1], (
                f"Monotonicity violated at index {i}: "
                f"Π({values[i]}) = {pi_values[i]} ≥ Π({values[i+1]}) = {pi_values[i+1]}"
            )


# ---------------------------------------------------------------------------
# Theorem 6.2 — Convergence
# ---------------------------------------------------------------------------

class TestIterateConvergence:
    def test_convergence_to_one(self) -> None:
        """Π^n(A) → 1 as n → ∞ for any positive finite f_A."""
        for f_A in [0.001, 0.5, 2.0, 1000.0]:
            trajectory = iterate_convergence(f_A, n_iterations=40)
            final = trajectory[-1]
            assert math.isclose(final, 1.0, abs_tol=1e-4), (
                f"Did not converge to 1 for f_A={f_A}; final value={final}"
            )

    def test_starting_from_one_stays_one(self) -> None:
        trajectory = iterate_convergence(1.0, n_iterations=10)
        for val in trajectory:
            assert math.isclose(val, 1.0, rel_tol=1e-12)

    def test_trajectory_length(self) -> None:
        n = 7
        trajectory = iterate_convergence(5.0, n_iterations=n)
        assert len(trajectory) == n + 1

    def test_trajectory_first_element_is_f_A(self) -> None:
        f_A = 3.14
        trajectory = iterate_convergence(f_A, n_iterations=5)
        assert math.isclose(trajectory[0], f_A, rel_tol=1e-12)

    def test_trajectory_second_element_is_pi_radical(self) -> None:
        f_A = 8.0
        trajectory = iterate_convergence(f_A, n_iterations=5)
        expected = pi_radical_significance(f_A)
        assert math.isclose(trajectory[1], expected, rel_tol=1e-12)

    def test_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="strictly positive"):
            iterate_convergence(0.0, n_iterations=5)
        with pytest.raises(ValueError, match="strictly positive"):
            iterate_convergence(-1.0, n_iterations=5)

    def test_compression_below_one(self) -> None:
        """For f_A < 1, each Π application *raises* the value toward 1."""
        f_A = 0.01
        trajectory = iterate_convergence(f_A, n_iterations=20)
        for i in range(1, len(trajectory)):
            assert trajectory[i] >= trajectory[i - 1] or math.isclose(
                trajectory[i], trajectory[i - 1], abs_tol=1e-10
            ), f"Value decreased at step {i}: {trajectory[i-1]} → {trajectory[i]}"

    def test_compression_above_one(self) -> None:
        """For f_A > 1, each Π application *lowers* the value toward 1."""
        f_A = 1000.0
        trajectory = iterate_convergence(f_A, n_iterations=20)
        for i in range(1, len(trajectory)):
            assert trajectory[i] <= trajectory[i - 1] or math.isclose(
                trajectory[i], trajectory[i - 1], abs_tol=1e-10
            ), f"Value increased at step {i}: {trajectory[i-1]} → {trajectory[i]}"
