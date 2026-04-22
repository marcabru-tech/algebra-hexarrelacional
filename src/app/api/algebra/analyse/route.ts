import { NextRequest, NextResponse } from 'next/server';
import { analyseCode, type AnalysisResult } from '@/lib/algebra-engine';

export async function POST(req: NextRequest) {
  try {
    const { code, referenceCode } = await req.json();
    if (!code) {
      return NextResponse.json({ error: 'Código obrigatório' }, { status: 400 });
    }
    const analysis: AnalysisResult = analyseCode(
      code as string,
      referenceCode as string | undefined,
    );
    return NextResponse.json({ analysis });
  } catch {
    return NextResponse.json({ error: 'Erro interno do servidor' }, { status: 500 });
  }
}
