import { NextRequest, NextResponse } from 'next/server';
import { piRadical, iterateConvergence, piRadicalSet } from '@/lib/algebra-engine';

export async function POST(req: NextRequest) {
  try {
    const { fA, setA, nIterations } = await req.json();
    const iterations: number = typeof nIterations === 'number' ? nIterations : 10;

    if (setA !== undefined) {
      if (!Array.isArray(setA) || (setA as unknown[]).some((v) => typeof v !== 'number')) {
        return NextResponse.json(
          { error: 'setA deve ser um array de números' },
          { status: 400 },
        );
      }
      const { convergence, iterations: totalIter, history } = piRadicalSet(
        setA as number[],
        (x: number) => piRadical(x),
        iterations,
      );
      return NextResponse.json({ convergence, iterations: totalIter, history });
    }

    if (fA !== undefined) {
      if (typeof fA !== 'number') {
        return NextResponse.json({ error: 'fA deve ser um número' }, { status: 400 });
      }
      if (fA < 0) {
        return NextResponse.json(
          { error: 'fA deve ser não-negativo' },
          { status: 400 },
        );
      }
      const result = piRadical(fA);
      const trajectory = fA > 0 ? iterateConvergence(fA, iterations) : [0];
      return NextResponse.json({ result, trajectory });
    }

    return NextResponse.json(
      { error: 'Forneça fA (escalar) ou setA (array)' },
      { status: 400 },
    );
  } catch {
    return NextResponse.json({ error: 'Erro interno do servidor' }, { status: 500 });
  }
}
