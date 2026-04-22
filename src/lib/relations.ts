/**
 * src/lib/relations.ts — The Six Significance Relations ρ₁–ρ₆ (TypeScript port).
 *
 * Theoretical basis (§0.3):
 *   ρ₁  Similitude     — surface similarity    (reflexive, symmetric, NOT transitive)
 *   ρ₂  Homologia      — structural sameness   (reflexive, transitive, NOT symmetric)
 *   ρ₃  Equivalência   — full substitutability (equivalence relation: R, S, T)
 *   ρ₄  Simetria       — group-orbit equality  (equivalence relation: R, S, T)
 *   ρ₅  Equilíbrio     — mutual cancellation   (symmetric, NOT reflexive, NOT transitive)
 *   ρ₆  Compensação    — emergent surplus value (most demanding — implies all above)
 *
 * All functions return a score in [0, 1] where 1 indicates perfect
 * satisfaction of the relation.
 */

export type RelationsProfile = {
  p1: number;
  p2: number;
  p3: number;
  p4: number;
  p5: number;
  p6: number;
};

// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

/** Map a string to a fixed-length character-frequency feature vector. */
function featureVector(s: string): number[] {
  const size = 64;
  const vec = new Array<number>(size).fill(0);
  for (let i = 0; i < s.length; i++) {
    vec[i % size] += s.charCodeAt(i) / 128.0;
  }
  const norm = Math.sqrt(vec.reduce((acc, v) => acc + v * v, 0));
  if (norm > 0) {
    for (let i = 0; i < vec.length; i++) vec[i] /= norm;
  }
  return vec;
}

/** Euclidean distance between two equal-length vectors. */
function euclidean(v1: number[], v2: number[]): number {
  let sum = 0;
  for (let i = 0; i < v1.length; i++) {
    const d = (v1[i] ?? 0) - (v2[i] ?? 0);
    sum += d * d;
  }
  return Math.sqrt(sum);
}

/** Character/token multiset for a string. */
function charMultiset(s: string): Map<string, number> {
  const ms = new Map<string, number>();
  const tokens = s.split(/\s+/).filter(Boolean);
  for (const tok of tokens) {
    ms.set(tok, (ms.get(tok) ?? 0) + 1);
  }
  return ms;
}

/** Default potential function: structural complexity centred at 0. */
function defaultPotential(s: string): number {
  const tokens = s.split(/\s+/).filter(Boolean);
  const rawComplexity = tokens.length;
  // Soft sigmoid, centred
  return 2.0 / (1.0 + Math.exp(-rawComplexity / 20.0)) - 1.0;
}

// ---------------------------------------------------------------------------
// ρ₁  Similitude
// ---------------------------------------------------------------------------

/**
 * ρ₁ Similitude: score proximity in a feature-embedding space.
 *
 * Properties: Reflexive, Symmetric, NOT transitive in general.
 */
export function calculateSimilitude(
  obj1: string,
  obj2: string,
  epsilon = 0.3,
): number {
  const v1 = featureVector(obj1);
  const v2 = featureVector(obj2);
  const dist = euclidean(v1, v2);
  return Math.exp(-dist / Math.max(epsilon, 1e-9));
}

// ---------------------------------------------------------------------------
// ρ₂  Homologia
// ---------------------------------------------------------------------------

/**
 * ρ₂ Homologia: score structural isomorphism (directional coverage).
 *
 * Formula: ρ₂(x, y) = Σ_k min(s₁[k], s₂[k]) / Σ_k s₁[k]
 *
 * Properties: Reflexive, Transitive, NOT symmetric in general.
 */
export function calculateHomology(obj1: string, obj2: string): number {
  const s1 = charMultiset(obj1);
  const s2 = charMultiset(obj2);
  const total1 = [...s1.values()].reduce((a, b) => a + b, 0);
  if (total1 === 0) return 1.0;
  let intersection = 0;
  for (const [k, v1] of s1) {
    intersection += Math.min(v1, s2.get(k) ?? 0);
  }
  return Math.min(intersection / total1, 1.0);
}

// ---------------------------------------------------------------------------
// ρ₃  Equivalência
// ---------------------------------------------------------------------------

/**
 * ρ₃ Equivalência: score functional substitutability.
 *
 * Properties: Reflexive, Symmetric, Transitive (true equivalence relation).
 */
export function calculateEquivalence(obj1: string, obj2: string): number {
  const structural = calculateHomology(obj1, obj2);
  const symBonus = calculateHomology(obj2, obj1);
  return Math.min((structural + symBonus) / 2.0, 1.0);
}

// ---------------------------------------------------------------------------
// ρ₄  Simetria
// ---------------------------------------------------------------------------

/**
 * ρ₄ Simetria: score the existence of a reversible group transformation.
 *
 * Default group: {identity, string-reversal}.
 * Properties: Reflexive, Symmetric, Transitive (group-orbit equivalence).
 */
export function calculateSymmetry(obj1: string, obj2: string): number {
  if (obj1 === obj2) return 1.0;
  if (obj1 === obj2.split('').reverse().join('')) return 1.0;
  if (obj2 === obj1.split('').reverse().join('')) return 1.0;
  // Continuous relaxation
  return calculateEquivalence(obj1, obj2) * 0.5;
}

// ---------------------------------------------------------------------------
// ρ₅  Equilíbrio
// ---------------------------------------------------------------------------

/**
 * ρ₅ Equilíbrio: score mutual cancellation of potentials.
 *
 * Properties: Symmetric, NOT reflexive in general, NOT transitive.
 */
export function calculateEquilibrium(
  obj1: string,
  obj2: string,
  potentialFunc?: (s: string) => number,
): number {
  const phi = potentialFunc ?? defaultPotential;
  const p1 = phi(obj1);
  const p2 = phi(obj2);
  const total = Math.abs(p1) + Math.abs(p2);
  if (total < 1e-12) return 1.0;
  const cancellation = 1.0 - Math.abs(p1 + p2) / total;
  return Math.max(cancellation, 0.0);
}

// ---------------------------------------------------------------------------
// ρ₆  Compensação
// ---------------------------------------------------------------------------

/**
 * ρ₆ Compensação: score the emergent surplus value of combining obj1+obj2.
 *
 * Weighted combination of all five prior relations.
 */
export function calculateCompensation(obj1: string, obj2: string): number {
  const r1 = calculateSimilitude(obj1, obj2);
  const r2 = (calculateHomology(obj1, obj2) + calculateHomology(obj2, obj1)) / 2.0;
  const r3 = calculateEquivalence(obj1, obj2);
  const r4 = calculateSymmetry(obj1, obj2);
  const r5 = calculateEquilibrium(obj1, obj2);
  const weights = [0.05, 0.10, 0.20, 0.25, 0.40];
  const scores = [r1, r2, r3, r4, r5];
  const base = weights.reduce((acc, w, i) => acc + w * (scores[i] ?? 0), 0);
  const synergy = Math.max(0.0, r5 - (r1 + r2 + r3 + r4) / 4.0) * 0.1;
  return Math.min(base + synergy, 1.0);
}

// ---------------------------------------------------------------------------
// Convenience: compute full relations profile
// ---------------------------------------------------------------------------

/**
 * Compute all six significance relations between two code strings.
 *
 * Returns a profile object { p1, p2, p3, p4, p5, p6 } where each value
 * is a score in [0, 1].
 */
export function computeRelations(obj1: string, obj2: string): RelationsProfile {
  return {
    p1: calculateSimilitude(obj1, obj2),
    p2: calculateHomology(obj1, obj2),
    p3: calculateEquivalence(obj1, obj2),
    p4: calculateSymmetry(obj1, obj2),
    p5: calculateEquilibrium(obj1, obj2),
    p6: calculateCompensation(obj1, obj2),
  };
}
