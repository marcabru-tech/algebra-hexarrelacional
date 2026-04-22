import { NextRequest, NextResponse } from 'next/server';
import { computeRelations, type RelationsProfile } from '@/lib/algebra-engine';

export async function POST(req: NextRequest) {
  try {
    const { code, referenceCode } = await req.json();
    if (!code) {
      return NextResponse.json({ error: 'Código obrigatório' }, { status: 400 });
    }
    if (!referenceCode) {
      return NextResponse.json(
        { error: 'Código de referência obrigatório' },
        { status: 400 },
      );
    }
    const relations: RelationsProfile = computeRelations(
      code,
      referenceCode,
    );
    return NextResponse.json({ relations });
  } catch {
    return NextResponse.json({ error: 'Erro interno do servidor' }, { status: 500 });
  }
}
