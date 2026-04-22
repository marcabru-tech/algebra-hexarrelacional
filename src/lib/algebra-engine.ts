/**
 * src/lib/algebra-engine.ts — Public façade for the algebra engine.
 *
 * Re-exports the functions used by Next.js API routes, providing a single
 * stable import path for all algebraic operations:
 *   - pyToJS / pyToRust  — lightweight pattern-based transpilation sketches
 *   - analyseCode        — full significance analysis (transpile + relations)
 *   - computeRelations   — six significance relations ρ₁–ρ₆
 *   - piRadical          — π-radical significance operator Π(A)
 *   - iterateConvergence — Theorem 6.2 convergence trajectory
 *   - piRadicalSet       — set-based π-radical with history
 */

// ---------------------------------------------------------------------------
// Transpilation sketches (pattern-based, no AST)
// ---------------------------------------------------------------------------

/**
 * Produce a lightweight JavaScript sketch from a Python source string.
 *
 * Pattern-based approximation suitable for the browser / edge runtime.
 * For production-quality transpilation, delegate to the Python `core.codegen`
 * layer via an external API.
 */
export function pyToJS(source: string): string {
  return source
    .replace(/^def (\w+)\((.*?)\):/gm, 'function $1($2) {')
    .replace(/^async def (\w+)\((.*?)\):/gm, 'async function $1($2) {')
    .replace(/^class (\w+):/gm, 'class $1 {')
    .replace(/\bTrue\b/g, 'true')
    .replace(/\bFalse\b/g, 'false')
    .replace(/\bNone\b/g, 'null')
    .replace(/\bprint\(/g, 'console.log(')
    .replace(/^(\s*)#(.*)$/gm, '$1//$2');
}

/**
 * Produce a lightweight Rust sketch from a Python source string.
 *
 * Same caveat as `pyToJS` — pattern-based, not AST-based.
 */
export function pyToRust(source: string): string {
  return source
    .replace(/^def (\w+)\((.*?)\):/gm, 'fn $1($2) {')
    .replace(/^async def (\w+)\((.*?)\):/gm, 'async fn $1($2) {')
    .replace(/^class (\w+):/gm, 'struct $1;')
    .replace(/\bTrue\b/g, 'true')
    .replace(/\bFalse\b/g, 'false')
    .replace(/\bNone\b/g, '()')
    .replace(/\bprint\(/g, 'println!(')
    .replace(/^(\s*)#(.*)$/gm, '$1//$2');
}

// ---------------------------------------------------------------------------
// Re-exports from existing modules
// ---------------------------------------------------------------------------

export { analyseCode, type AnalysisResult } from './engine';
export { computeRelations, type RelationsProfile } from './relations';
export {
  piRadicalSignificance as piRadical,
  iterateConvergence,
  calculatePiRadical as piRadicalSet,
  PI,
  INV_PI,
} from './operator';
