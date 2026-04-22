/**
 * src/lib/engine.ts — Algebraic engine: transpilation + significance relations.
 *
 * Provides the main `analyseCode` function that:
 *   1. Records the original Python source.
 *   2. Produces JavaScript and Rust transpilation sketches (process step).
 *   3. Computes all six significance relations (distribution step).
 *
 * The result shape mirrors the theoretical pipeline described in §0.2:
 *   𝕆 Operacionalizar → ℙ Processar → 𝔻 Distribuir → relations profile
 */

import { computeRelations, type RelationsProfile } from './relations';

// ---------------------------------------------------------------------------
// Transpilation helpers (client-side sketches)
// ---------------------------------------------------------------------------

/**
 * Produce a lightweight JavaScript sketch from a Python source string.
 *
 * This is a pattern-based approximation suitable for the browser without
 * a full AST parser.  For production-quality transpilation, delegate to
 * the Python `core.codegen` layer via an API route.
 */
function pythonToJsSketch(source: string): string {
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
 * Same caveat as `pythonToJsSketch` — pattern-based, not AST-based.
 */
function pythonToRustSketch(source: string): string {
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
// Public result type
// ---------------------------------------------------------------------------

export type AnalysisResult = {
  original: { code: string; language: string };
  process: { javascript: string; rust: string };
  distribution: RelationsProfile;
};

// ---------------------------------------------------------------------------
// Main engine function
// ---------------------------------------------------------------------------

/**
 * Analyse a Python code string and produce a significance profile.
 *
 * @param code - Python source code to analyse.
 * @param referenceCode - Optional reference code for relation computation.
 *   When omitted, the relations are computed between the original code
 *   and its own JavaScript transpilation sketch (self-comparison axis).
 * @returns An {@link AnalysisResult} containing:
 *   - `original`: the input code and its declared language,
 *   - `process`: lightweight JS and Rust transpilation sketches,
 *   - `distribution`: the six significance relation scores { p1 … p6 }.
 */
export function analyseCode(
  code: string,
  referenceCode?: string,
): AnalysisResult {
  const js = pythonToJsSketch(code);
  const rs = pythonToRustSketch(code);

  const ref = referenceCode ?? js;
  const rels = computeRelations(code, ref);

  return {
    original: { code, language: 'python' },
    process: { javascript: js, rust: rs },
    distribution: {
      p1: rels.p1,
      p2: rels.p2,
      p3: rels.p3,
      p4: rels.p4,
      p5: rels.p5,
      p6: rels.p6,
    },
  };
}
