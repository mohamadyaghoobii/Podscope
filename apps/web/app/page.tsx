"use client";

import { useEffect, useMemo, useState } from "react";
import { AnalysisResult, ExampleManifest, RuleInfo, analyzeManifest, getExamples, getRules } from "../lib/api";
import { FindingList } from "../components/FindingList";
import { ScoreRing } from "../components/ScoreRing";

const fallbackManifest = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: storefront
  namespace: prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: storefront
  template:
    metadata:
      labels:
        app: storefront
    spec:
      containers:
        - name: web
          image: nginx:latest`;

export default function HomePage() {
  const [manifestName, setManifestName] = useState("workload.yaml");
  const [content, setContent] = useState(fallbackManifest);
  const [examples, setExamples] = useState<ExampleManifest[]>([]);
  const [rules, setRules] = useState<RuleInfo[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getExamples().then(setExamples).catch(() => setExamples([]));
    getRules().then(setRules).catch(() => setRules([]));
  }, []);

  const totalFindings = useMemo(() => result?.findings.length || 0, [result]);

  async function runAnalysis() {
    setLoading(true);
    setError(null);
    try {
      const analysis = await analyzeManifest(manifestName, content);
      setResult(analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  function loadExample(example: ExampleManifest) {
    setManifestName(example.name);
    setContent(example.content);
    setResult(null);
    setError(null);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">P</div>
        <div>
          <div className="brand-title">Podscope</div>
          <div className="brand-subtitle">Kubernetes manifest review</div>
        </div>
        <nav>
          <a className="active">Analyze</a>
          <a>Rules</a>
          <a>Reports</a>
          <a>Integrations</a>
        </nav>
      </aside>

      <section className="main-panel">
        <header className="hero">
          <div>
            <p className="eyebrow">Static review for platform teams</p>
            <h1>Find risky Kubernetes workload patterns before they reach the cluster.</h1>
            <p className="hero-copy">Paste or upload manifest bundles, review baseline security and reliability findings, and hand engineers practical remediation hints.</p>
          </div>
          <div className="hero-card">
            <div className="metric-number">{rules.length || 13}</div>
            <div className="metric-label">built-in checks</div>
          </div>
        </header>

        <section className="grid two-column">
          <div className="panel editor-panel">
            <div className="panel-head">
              <div>
                <h2>Manifest input</h2>
                <p>Multi-document YAML is supported.</p>
              </div>
              <button className="primary-button" onClick={runAnalysis} disabled={loading}>{loading ? "Analyzing..." : "Run review"}</button>
            </div>

            <label className="field-label">Bundle name</label>
            <input className="text-input" value={manifestName} onChange={(event) => setManifestName(event.target.value)} />

            <label className="field-label">Kubernetes YAML</label>
            <textarea className="yaml-editor" value={content} onChange={(event) => setContent(event.target.value)} spellCheck={false} />

            <div className="example-row">
              {examples.map((example) => (
                <button key={example.name} className="secondary-button" onClick={() => loadExample(example)}>{example.name}</button>
              ))}
            </div>
            {error ? <div className="error-box">{error}</div> : null}
          </div>

          <div className="panel result-panel">
            <div className="panel-head">
              <div>
                <h2>Review summary</h2>
                <p>{result ? `${totalFindings} findings across ${result.resource_count} resources` : "Run a review to see score, findings, and remediation."}</p>
              </div>
            </div>
            {result ? (
              <>
                <div className="summary-grid">
                  <ScoreRing score={result.score} />
                  <div className="mini-stat"><strong>{result.workload_count}</strong><span>workloads</span></div>
                  <div className="mini-stat"><strong>{result.namespace_count}</strong><span>namespaces</span></div>
                  <div className="mini-stat"><strong>{result.status}</strong><span>status</span></div>
                </div>
                <div className="severity-grid">
                  {Object.entries(result.severity_counts).map(([severity, count]) => (
                    <div className="severity-cell" key={severity}>
                      <span>{severity}</span>
                      <strong>{count}</strong>
                    </div>
                  ))}
                </div>
                <FindingList findings={result.findings} />
              </>
            ) : (
              <div className="empty-state tall">No review has been run yet.</div>
            )}
          </div>
        </section>

        <section className="panel rules-panel">
          <div className="panel-head">
            <div>
              <h2>Baseline rule set</h2>
              <p>Focused on workload hardening, exposure, RBAC, and operational readiness.</p>
            </div>
          </div>
          <div className="rule-grid">
            {rules.map((rule) => (
              <article className="rule-card" key={rule.rule_id}>
                <div className="rule-id">{rule.rule_id}</div>
                <h3>{rule.title}</h3>
                <p>{rule.description}</p>
                <span>{rule.category}</span>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
