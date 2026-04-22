/**
 * src/lib/operator.ts — The π-radical significance operator Π(A) = [f(A)]^(1/π).
 *
 * Theoretical basis (§0.1):
 *   Π(A) := [f(A)]^(1/π)  where π = 3.14159...
 *
 * Key properties:
 *   1. Irredutibility — the exponent 1/π is transcendental.
 *   2. Compression — compresses peaks and raises minima toward 1.
 *   3. Convergence (Theorem 6.2) — iterating Π drives any positive finite
 *      value toward 1: lim_{n→∞} (f_A)^{(1/π)^n} = 1 for f_A > 0.
 */

export const PI: number = Math.PI;
export const INV_PI: number = 1.0 / Math.PI;

// ---------------------------------------------------------------------------
// Core operator
// ---------------------------------------------------------------------------

/**
 * Compute the π-radical significance of a non-negative scalar f(A).
 *
 * Π(A) = [f(A)]^(1/π)
 *
 * @param fA - The significance score f(A). Must be non-negative.
 * @returns The π-radical of fA, a value in ℝ≥0.
 * @throws {RangeError} If fA is negative.
 */
export function piRadicalSignificance(fA: number): number {
  if (fA < 0) {
    throw new RangeError(`f(A) must be non-negative; got ${fA}.`);
  }
  if (fA === 0) return 0.0;
  return Math.pow(fA, INV_PI);
}

// ---------------------------------------------------------------------------
// Iterative convergence (Theorem 6.2)
// ---------------------------------------------------------------------------

/**
 * Demonstrate Theorem 6.2: iterative application of Π converges to 1.
 *
 * Each step applies the π-radical to the previous result:
 *   Π^(k)(A) = [Π^(k-1)(A)]^(1/π)
 *
 * @param fA - Initial significance score f(A) > 0.
 * @param nIterations - Number of successive Π applications to compute.
 * @returns Array of length nIterations + 1: [f_A, Π(f_A), Π²(f_A), …, Πⁿ(f_A)].
 * @throws {RangeError} If fA is not strictly positive.
 */
export function iterateConvergence(
  fA: number,
  nIterations = 10,
): number[] {
  if (fA <= 0) {
    throw new RangeError(
      `f(A) must be strictly positive for convergence; got ${fA}.`,
    );
  }
  const trajectory: number[] = [fA];
  let current = fA;
  for (let i = 0; i < nIterations; i++) {
    current = piRadicalSignificance(current);
    trajectory.push(current);
  }
  return trajectory;
}

// ---------------------------------------------------------------------------
// Set-based π-radical operator
// ---------------------------------------------------------------------------

/**
 * Apply the function f iteratively to each element of setA and track
 * the history of transformations.
 *
 * @param setA - The initial set of numeric values.
 * @param f - A function applied element-wise at each iteration.
 * @param iterations - Number of iterations to perform (default: 10).
 * @returns An object containing:
 *   - `convergence`: the final state of the set after all iterations,
 *   - `iterations`: total number of states in history (initial + applied),
 *   - `history`: array of all intermediate states including the initial one.
 */
export function calculatePiRadical(
  setA: number[],
  f: (x: number) => number,
  iterations = 10,
): { convergence: number[]; iterations: number; history: number[][] } {
  let current = [...setA];
  const history = [current.slice()];
  for (let i = 0; i < iterations; i++) {
    current = current.map((x) => f(x));
    history.push(current.slice());
  }
  return {
    convergence: history[history.length - 1]!,
    iterations: history.length,
    history,
  };
}
