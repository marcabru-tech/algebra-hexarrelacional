"use client";
import { useState } from 'react';
import { t, isRtl, Lang, getSupportedLangs, getLangLabel } from '@/lib/i18n';

type Tab = 'transpile' | 'relations' | 'analyse' | 'operator' | 'projects';

type Project = {
  id: string;
  name: string;
  code: string;
  refCode: string;
  createdAt: string;
};

type TranspileResult = { javascript?: string; rust?: string };
type RelationsResult = { p1: number; p2: number; p3: number; p4: number; p5: number; p6: number };
type AnalysisResult = {
  original: { code: string; language: string };
  process: { javascript: string; rust: string };
  distribution: RelationsResult;
};
type OperatorResult = {
  result?: number;
  trajectory?: number[];
  convergence?: number[];
  iterations?: number;
  history?: number[][];
};

export default function Home() {
  const [tab, setTab] = useState<Tab>('transpile');
  const [lang, setLang] = useState<Lang>('pt_BR');
  const [code, setCode] = useState('def fibonacci(n):\n  if n <= 1:\n    return n\n  return fibonacci(n-1) + fibonacci(n-2)\n\nprint(fibonacci(10))');
  const [refCode, setRefCode] = useState('');
  const [output, setOutput] = useState('');
  const [status, setStatus] = useState('ready');
  const [projects, setProjects] = useState<Project[]>([]);

  // Operator tab state
  const [fA, setFA] = useState('0.5');
  const [setA, setSetA] = useState('0.1, 0.5, 0.9');
  const [nIterations, setNIterations] = useState('10');
  const [useSet, setUseSet] = useState(false);

  // Typed result states
  const [transpileResult, setTranspileResult] = useState<TranspileResult | null>(null);
  const [relationsResult, setRelationsResult] = useState<RelationsResult | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [operatorResult, setOperatorResult] = useState<OperatorResult | null>(null);

  const dir = isRtl(lang) ? 'rtl' : 'ltr';

  async function handleTranspile() {
    setStatus('loading');
    setOutput('');
    setTranspileResult(null);
    try {
      const res = await fetch('/api/algebra/transpile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const data = await res.json();
      if (!res.ok) {
        setOutput(data.error ?? t('error.run.timeout', lang));
        setStatus('error');
      } else {
        setTranspileResult(data.result as TranspileResult);
        setStatus('ready');
      }
    } catch {
      setOutput(t('error.run.timeout', lang));
      setStatus('error');
    }
  }

  async function handleRelations() {
    setStatus('loading');
    setOutput('');
    setRelationsResult(null);
    try {
      const res = await fetch('/api/algebra/relations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, referenceCode: refCode }),
      });
      const data = await res.json();
      if (!res.ok) {
        setOutput(data.error ?? t('error.run.timeout', lang));
        setStatus('error');
      } else {
        setRelationsResult(data.relations as RelationsResult);
        setStatus('ready');
      }
    } catch {
      setOutput(t('error.run.timeout', lang));
      setStatus('error');
    }
  }

  async function handleAnalyse() {
    setStatus('loading');
    setOutput('');
    setAnalysisResult(null);
    try {
      const res = await fetch('/api/algebra/analyse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, referenceCode: refCode || undefined }),
      });
      const data = await res.json();
      if (!res.ok) {
        setOutput(data.error ?? t('error.run.timeout', lang));
        setStatus('error');
      } else {
        setAnalysisResult(data.analysis as AnalysisResult);
        setStatus('ready');
      }
    } catch {
      setOutput(t('error.run.timeout', lang));
      setStatus('error');
    }
  }

  async function handleOperator() {
    setStatus('loading');
    setOutput('');
    setOperatorResult(null);
    try {
      const body: Record<string, unknown> = { nIterations: Number(nIterations) };
      if (useSet) {
        body.setA = setA.split(',').map((v: string) => Number(v.trim())).filter((v: number) => !isNaN(v));
      } else {
        body.fA = Number(fA);
      }
      const res = await fetch('/api/algebra/operator', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        setOutput(data.error ?? t('error.run.timeout', lang));
        setStatus('error');
      } else {
        setOperatorResult(data as OperatorResult);
        setStatus('ready');
      }
    } catch {
      setOutput(t('error.run.timeout', lang));
      setStatus('error');
    }
  }

  function handleSaveProject() {
    const name = prompt(t('prompt.project_name', lang));
    if (!name) return;
    const project: Project = {
      id: Date.now().toString(),
      name,
      code,
      refCode,
      createdAt: new Date().toISOString(),
    };
    setProjects((prev: Project[]) => [...prev, project]);
  }

  function handleLoadProject(project: Project) {
    setCode(project.code);
    setRefCode(project.refCode);
    setTab('transpile');
  }

  function handleDeleteProject(id: string) {
    setProjects((prev: Project[]) => prev.filter((p: Project) => p.id !== id));
  }

  const RELATION_LABELS: Record<string, string> = {
    p1: 'ρ₁ Similitude',
    p2: 'ρ₂ Homologia',
    p3: 'ρ₃ Equivalência',
    p4: 'ρ₄ Simetria',
    p5: 'ρ₅ Equilíbrio',
    p6: 'ρ₆ Compensação',
  };

  return (
    <main dir={dir} style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 900, margin: '0 auto', padding: '1rem' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.4rem', margin: 0 }}>{t('app.name', lang)}</h1>
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value as Lang)}
          aria-label="Language selector"
          style={{ padding: '0.3rem 0.5rem' }}
        >
          {getSupportedLangs().map((l) => (
            <option key={l} value={l}>
              {getLangLabel(l, lang)}
            </option>
          ))}
        </select>
      </header>

      {/* Tabs */}
      <nav style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {(['transpile', 'relations', 'analyse', 'operator', 'projects'] as Tab[]).map((tabKey) => (
          <button
            key={tabKey}
            onClick={() => setTab(tabKey)}
            style={{
              padding: '0.4rem 0.9rem',
              background: tab === tabKey ? '#0070f3' : '#eee',
              color: tab === tabKey ? '#fff' : '#333',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontWeight: tab === tabKey ? 700 : 400,
            }}
          >
            {tabKey === 'transpile' && t('nav.dashboard', lang)}
            {tabKey === 'relations' && t('nav.relations', lang)}
            {tabKey === 'analyse' && t('nav.analyse', lang)}
            {tabKey === 'operator' && t('nav.operators', lang)}
            {tabKey === 'projects' && t('nav.projects', lang)}
          </button>
        ))}
      </nav>

      {/* Shared code editor (shown on transpile / relations / analyse tabs) */}
      {(tab === 'transpile' || tab === 'relations' || tab === 'analyse') && (
        <section style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>
            {tab === 'transpile' ? 'Python code' : 'Code'}
          </label>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            rows={8}
            style={{ width: '100%', fontFamily: 'monospace', fontSize: '0.9rem', padding: '0.5rem', boxSizing: 'border-box' }}
          />
          {(tab === 'relations' || tab === 'analyse') && (
            <>
              <label style={{ display: 'block', marginTop: '0.75rem', marginBottom: 4, fontWeight: 600 }}>
                Reference code {tab === 'analyse' && '(optional)'}
              </label>
              <textarea
                value={refCode}
                onChange={(e) => setRefCode(e.target.value)}
                rows={5}
                style={{ width: '100%', fontFamily: 'monospace', fontSize: '0.9rem', padding: '0.5rem', boxSizing: 'border-box' }}
              />
            </>
          )}
        </section>
      )}

      {/* Tab: Transpile */}
      {tab === 'transpile' && (
        <section>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <button
              onClick={handleTranspile}
              disabled={status === 'loading'}
              style={{ padding: '0.5rem 1.2rem', background: '#0070f3', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
            >
              {status === 'loading' ? 'Transpiling…' : 'Transpile'}
            </button>
            <button
              onClick={handleSaveProject}
              style={{ padding: '0.5rem 1rem', background: '#28a745', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
            >
              Save project
            </button>
          </div>
          {status === 'error' && output && (
            <p style={{ color: 'red' }}>{output}</p>
          )}
          {transpileResult && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <h3 style={{ marginTop: 0 }}>JavaScript</h3>
                <pre style={{ background: '#f5f5f5', padding: '0.75rem', borderRadius: 4, overflowX: 'auto', fontSize: '0.85rem' }}>
                  {transpileResult.javascript}
                </pre>
              </div>
              <div>
                <h3 style={{ marginTop: 0 }}>Rust</h3>
                <pre style={{ background: '#f5f5f5', padding: '0.75rem', borderRadius: 4, overflowX: 'auto', fontSize: '0.85rem' }}>
                  {transpileResult.rust}
                </pre>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Tab: Relations */}
      {tab === 'relations' && (
        <section>
          <button
            onClick={handleRelations}
            disabled={status === 'loading'}
            style={{ padding: '0.5rem 1.2rem', background: '#0070f3', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', marginBottom: '1rem' }}
          >
            {status === 'loading' ? 'Computing…' : 'Compute Relations'}
          </button>
          {status === 'error' && output && (
            <p style={{ color: 'red' }}>{output}</p>
          )}
          {relationsResult && (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Relation</th>
                  <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Score</th>
                  <th style={{ padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Bar</th>
                </tr>
              </thead>
              <tbody>
                {(Object.keys(RELATION_LABELS) as (keyof RelationsResult)[]).map((key) => (
                  <tr key={key}>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{RELATION_LABELS[key]}</td>
                    <td style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '1px solid #eee', fontVariantNumeric: 'tabular-nums' }}>
                      {(relationsResult[key] * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                      <div style={{ background: '#eee', borderRadius: 4, height: 16, width: '100%', minWidth: 80 }}>
                        <div style={{ background: '#0070f3', borderRadius: 4, height: '100%', width: `${(relationsResult[key] * 100).toFixed(1)}%` }} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {/* Tab: Analyse */}
      {tab === 'analyse' && (
        <section>
          <button
            onClick={handleAnalyse}
            disabled={status === 'loading'}
            style={{ padding: '0.5rem 1.2rem', background: '#0070f3', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', marginBottom: '1rem' }}
          >
            {status === 'loading' ? 'Analysing…' : 'Analyse'}
          </button>
          {status === 'error' && output && (
            <p style={{ color: 'red' }}>{output}</p>
          )}
          {analysisResult && (
            <div>
              <h3>Original ({analysisResult.original.language})</h3>
              <pre style={{ background: '#f5f5f5', padding: '0.75rem', borderRadius: 4, fontSize: '0.85rem', overflowX: 'auto' }}>
                {analysisResult.original.code}
              </pre>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                <div>
                  <h4 style={{ marginTop: 0 }}>JavaScript</h4>
                  <pre style={{ background: '#f5f5f5', padding: '0.75rem', borderRadius: 4, fontSize: '0.85rem', overflowX: 'auto' }}>
                    {analysisResult.process.javascript}
                  </pre>
                </div>
                <div>
                  <h4 style={{ marginTop: 0 }}>Rust</h4>
                  <pre style={{ background: '#f5f5f5', padding: '0.75rem', borderRadius: 4, fontSize: '0.85rem', overflowX: 'auto' }}>
                    {analysisResult.process.rust}
                  </pre>
                </div>
              </div>
              <h3>Significance Relations</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Relation</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(Object.keys(RELATION_LABELS) as (keyof RelationsResult)[]).map((key) => (
                    <tr key={key}>
                      <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{RELATION_LABELS[key]}</td>
                      <td style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '1px solid #eee', fontVariantNumeric: 'tabular-nums' }}>
                        {(analysisResult.distribution[key] * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* Tab: Operator */}
      {tab === 'operator' && (
        <section>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Mode</label>
            <label style={{ marginRight: '1rem' }}>
              <input type="radio" checked={!useSet} onChange={() => setUseSet(false)} /> Scalar (fA)
            </label>
            <label>
              <input type="radio" checked={useSet} onChange={() => setUseSet(true)} /> Set (setA)
            </label>
          </div>
          {!useSet ? (
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>f(A) value</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={fA}
                onChange={(e) => setFA(e.target.value)}
                style={{ padding: '0.4rem', width: 160 }}
              />
            </div>
          ) : (
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>setA (comma-separated numbers)</label>
              <input
                type="text"
                value={setA}
                onChange={(e) => setSetA(e.target.value)}
                style={{ padding: '0.4rem', width: '100%', boxSizing: 'border-box' }}
              />
            </div>
          )}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Iterations</label>
            <input
              type="number"
              min="1"
              max="100"
              value={nIterations}
              onChange={(e) => setNIterations(e.target.value)}
              style={{ padding: '0.4rem', width: 100 }}
            />
          </div>
          <button
            onClick={handleOperator}
            disabled={status === 'loading'}
            style={{ padding: '0.5rem 1.2rem', background: '#0070f3', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', marginBottom: '1rem' }}
          >
            {status === 'loading' ? 'Computing…' : 'Compute Π'}
          </button>
          {status === 'error' && output && (
            <p style={{ color: 'red' }}>{output}</p>
          )}
          {operatorResult && !useSet && operatorResult.result !== undefined && (
            <div>
              <p><strong>Π(A) = {operatorResult.result.toFixed(6)}</strong></p>
              {operatorResult.trajectory && (
                <div>
                  <h4>Convergence trajectory</h4>
                  <ol start={0} style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
                    {operatorResult.trajectory.map((v, i) => (
                      <li key={i} style={{ listStylePosition: 'inside' }}>Π<sup>{i}</sup>(A) = {v.toFixed(8)}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
          {operatorResult && useSet && operatorResult.convergence !== undefined && (
            <div>
              <h4>Convergence (after {operatorResult.iterations} steps)</h4>
              <pre style={{ background: '#f5f5f5', padding: '0.75rem', borderRadius: 4, fontSize: '0.85rem' }}>
                {JSON.stringify(operatorResult.convergence, null, 2)}
              </pre>
            </div>
          )}
        </section>
      )}

      {/* Tab: Projects */}
      {tab === 'projects' && (
        <section>
          <h2 style={{ marginTop: 0 }}>Saved Projects</h2>
          {projects.length === 0 ? (
            <p style={{ color: '#666' }}>{t('projects.empty', lang)}</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Name</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Created</th>
                  <th style={{ padding: '0.5rem', borderBottom: '2px solid #ddd' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project) => (
                  <tr key={project.id}>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{project.name}</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee', color: '#666', fontSize: '0.85rem' }}>
                      {new Date(project.createdAt).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                      <button
                        onClick={() => handleLoadProject(project)}
                        style={{ marginRight: '0.5rem', padding: '0.3rem 0.7rem', background: '#0070f3', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                      >
                        Load
                      </button>
                      <button
                        onClick={() => handleDeleteProject(project.id)}
                        style={{ padding: '0.3rem 0.7rem', background: '#dc3545', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {/* Status bar */}
      <footer style={{ marginTop: '2rem', color: '#888', fontSize: '0.8rem', borderTop: '1px solid #eee', paddingTop: '0.5rem' }}>
        Status: {status}
      </footer>
    </main>
  );
}
