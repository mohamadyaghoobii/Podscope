"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AnalysisResult,
  ExampleManifest,
  RuleInfo,
  Severity,
  analyzeManifest,
  getExamples,
  getRules
} from "../lib/api";
import { ManifestEditor } from "../components/ManifestEditor";
import { ScoreCard } from "../components/ScoreCard";
import { CategoryBreakdown, SeverityBreakdown, StatTiles } from "../components/Breakdown";
import { FindingsPanel } from "../components/FindingsPanel";
import { ResourceMap } from "../components/ResourceMap";
import { AiPanel } from "../components/AiPanel";
import { RulesView } from "../components/RulesView";
import { ExamplesView } from "../components/ExamplesView";
import { DocsView } from "../components/DocsView";
import { BookIcon, LayersIcon, RulesIcon, ScopeIcon } from "../components/icons";

type View = "review" | "rules" | "examples" | "docs";
type ResultTab = "findings" | "resources" | "assistant";

const STARTER = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  namespace: prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: checkout
  template:
    metadata:
      labels:
        app: checkout
    spec:
      containers:
        - name: web
          image: nginx:latest
          securityContext:
            privileged: true`;

const NAV: Array<{ id: View; label: string; Icon: typeof ScopeIcon }> = [
  { id: "review", label: "Review", Icon: ScopeIcon },
  { id: "rules", label: "Rules", Icon: RulesIcon },
  { id: "examples", label: "Examples", Icon: LayersIcon },
  { id: "docs", label: "Docs", Icon: BookIcon }
];

export default function HomePage() {
  const [view, setView] = useState<View>("review");
  const [resultTab, setResultTab] = useState<ResultTab>("findings");
  const [name, setName] = useState("checkout.yaml");
  const [content, setContent] = useState(STARTER);
  const [strict, setStrict] = useState(false);
  const [examples, setExamples] = useState<ExampleManifest[]>([]);
  const [rules, setRules] = useState<RuleInfo[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzedContent, setAnalyzedContent] = useState("");
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");

  useEffect(() => {
    getExamples().then(setExamples).catch(() => setExamples([]));
    getRules().then(setRules).catch(() => setRules([]));
  }, []);

  const filteredFindings = useMemo(() => {
    if (!result) return [];
    if (severityFilter === "all") return result.findings;
    return result.findings.filter((finding) => finding.severity === severityFilter);
  }, [result, severityFilter]);

  async function runAnalysis(nextContent = content, nextName = name) {
    setLoading(true);
    setError(null);
    try {
      const analysis = await analyzeManifest(nextName, nextContent, { strict });
      setResult(analysis);
      setAnalyzedContent(nextContent);
      setSeverityFilter("all");
      setResultTab("findings");
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  function loadExample(example: ExampleManifest, analyze = false) {
    setName(example.name);
    setContent(example.content);
    setError(null);
    setView("review");
    if (analyze) {
      void runAnalysis(example.content, example.name);
    } else {
      setResult(null);
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">
            <ScopeIcon className="icon-sm" />
          </span>
          <div>
            <div className="brand-name">Podscope</div>
            <div className="brand-tag">Kubernetes review</div>
          </div>
        </div>
        <nav className="nav">
          {NAV.map(({ id, label, Icon }) => (
            <button key={id} className={`nav-item ${view === id ? "is-active" : ""}`} onClick={() => setView(id)}>
              <Icon className="icon-sm" />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="status-line">
            <span className="status-dot" />
            Local engine · {rules.length || "43"} rules
          </div>
          <p>Standalone module of the OpsDeck DevSecOps platform.</p>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <h1>{NAV.find((item) => item.id === view)?.label}</h1>
            <p className="topbar-sub">
              {view === "review" && "Catch risky workload, RBAC, exposure, and reliability issues before deploy."}
              {view === "rules" && "The deterministic checks behind every Podscope review."}
              {view === "examples" && "Curated manifests to explore the analyzer."}
              {view === "docs" && "Scoring, categories, and integration."}
            </p>
          </div>
          {view === "review" && (
            <button className="primary-button header-run" onClick={() => runAnalysis()} disabled={loading}>
              {loading ? "Analyzing…" : "Run review"}
            </button>
          )}
        </header>

        {view === "review" && (
          <div className="workspace">
            <section className="panel editor-panel">
              <ManifestEditor
                name={name}
                value={content}
                examples={examples}
                loading={loading}
                strict={strict}
                onNameChange={setName}
                onChange={setContent}
                onLoadExample={(example) => loadExample(example, false)}
                onStrictChange={setStrict}
                onRun={() => runAnalysis()}
              />
            </section>

            <section className="results">
              {error && (
                <div className="panel error-panel">
                  <div className="error-title">Could not analyze manifest</div>
                  <p>{error}</p>
                </div>
              )}

              {!result && !error && (
                <div className="panel empty-hero">
                  <div className="empty-hero-glyph">
                    <ScopeIcon className="icon-lg" />
                  </div>
                  <h2>Run a review to see results</h2>
                  <p>Paste a manifest, drop a YAML file, or load a sample. Podscope returns a score, grouped findings, and copy-ready fixes.</p>
                  <div className="empty-hero-samples">
                    {examples.slice(0, 3).map((example) => (
                      <button key={example.name} className="ghost-button" onClick={() => loadExample(example, true)}>
                        Try “{example.title}”
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {loading && !result && (
                <div className="panel loading-panel">
                  <div className="spinner" />
                  <span>Reviewing manifest…</span>
                </div>
              )}

              {result && (
                <>
                  <div className="panel scorecard-panel">
                    <ScoreCard card={result.scorecard} />
                    <p className="result-summary">{result.summary}</p>
                    <StatTiles result={result} />
                  </div>

                  <div className="panel breakdown-panel">
                    <div className="panel-section">
                      <h3>Severity</h3>
                      <SeverityBreakdown counts={result.severity_counts} active={severityFilter} onSelect={setSeverityFilter} />
                    </div>
                    {result.category_counts.length > 0 && (
                      <div className="panel-section">
                        <h3>By category</h3>
                        <CategoryBreakdown result={result} />
                      </div>
                    )}
                  </div>

                  <div className="panel result-tabs-panel">
                    <div className="result-tabs">
                      <button className={resultTab === "findings" ? "is-active" : ""} onClick={() => setResultTab("findings")}>
                        Findings <span>{result.findings.length}</span>
                      </button>
                      <button className={resultTab === "resources" ? "is-active" : ""} onClick={() => setResultTab("resources")}>
                        Resources <span>{result.resource_count}</span>
                      </button>
                      <button className={resultTab === "assistant" ? "is-active" : ""} onClick={() => setResultTab("assistant")}>
                        Assistant
                      </button>
                    </div>

                    <div className="result-tab-body">
                      {resultTab === "findings" && (
                        <>
                          {severityFilter !== "all" && (
                            <button className="clear-filter" onClick={() => setSeverityFilter("all")}>
                              Clear {severityFilter} filter ×
                            </button>
                          )}
                          <FindingsPanel findings={filteredFindings} />
                        </>
                      )}
                      {resultTab === "resources" && <ResourceMap result={result} />}
                      {resultTab === "assistant" && <AiPanel name={name} content={analyzedContent || content} />}
                    </div>
                  </div>

                  {result.next_steps.length > 0 && resultTab === "findings" && (
                    <div className="panel next-steps">
                      <h3>Recommended next steps</h3>
                      <ol>
                        {result.next_steps.map((step, index) => (
                          <li key={index}>{step}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                </>
              )}
            </section>
          </div>
        )}

        {view === "rules" && <RulesView rules={rules} />}
        {view === "examples" && <ExamplesView examples={examples} onLoad={(example) => loadExample(example, true)} />}
        {view === "docs" && <DocsView />}
      </main>
    </div>
  );
}
