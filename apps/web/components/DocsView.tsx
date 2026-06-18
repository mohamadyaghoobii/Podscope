const categories = [
  ["Workload Security", "Privilege, capabilities, host namespaces, image pinning, and container hardening."],
  ["RBAC", "Wildcard rules, cluster-admin bindings, broad subjects, and Secret access."],
  ["Network Exposure", "LoadBalancer and NodePort services, ingress TLS, and NetworkPolicy coverage."],
  ["Secrets", "Hardcoded credentials, secret-like ConfigMap values, and unsafe Secret handling."],
  ["Reliability", "Requests, limits, probes, replicas, disruption budgets, and spread."],
  ["Hygiene", "Recommended labels, namespace placement, and ownership metadata."]
];

export function DocsView() {
  return (
    <div className="docs-view">
      <div className="view-head">
        <h2>How Podscope works</h2>
        <p>Static review for Kubernetes manifests. Deterministic by design, with an optional AI layer.</p>
      </div>

      <section className="docs-section">
        <h3>Scoring model</h3>
        <p>
          Every review starts at <strong>100</strong>. Each finding subtracts points weighted by severity and confidence,
          and the score is capped at 0. The grade (A–F) and status (Deployable / Needs review / Blocked) follow from the
          score, and any critical finding forces a Blocked status.
        </p>
        <div className="score-formula">
          <span>critical −25</span>
          <span>high −12</span>
          <span>medium −6</span>
          <span>low −2</span>
          <span>info 0</span>
          <span className="formula-note">× confidence factor</span>
        </div>
      </section>

      <section className="docs-section">
        <h3>Rule categories</h3>
        <div className="docs-cards">
          {categories.map(([title, body]) => (
            <div className="docs-card" key={title}>
              <h4>{title}</h4>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="docs-section">
        <h3>Integration with OpsDeck</h3>
        <p>
          Every review is returned as a stable, versioned JSON contract (<code>schema_version</code>, scorecard, findings,
          and resource summaries). OpsDeck can ingest that payload directly to combine Kubernetes review with the rest of
          the platform — no scraping, no UI coupling.
        </p>
      </section>
    </div>
  );
}
