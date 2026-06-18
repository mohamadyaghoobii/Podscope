import { Finding, Severity } from "../lib/api";
import { SEVERITY_LABEL, SEVERITY_ORDER } from "../lib/format";
import { FindingCard } from "./FindingCard";

export function FindingsPanel({ findings }: { findings: Finding[] }) {
  if (!findings.length) {
    return (
      <div className="empty-state">
        <div className="empty-emoji">✓</div>
        <p>No findings match the current filter.</p>
      </div>
    );
  }

  const grouped = SEVERITY_ORDER.map((severity) => ({
    severity,
    items: findings.filter((finding) => finding.severity === severity)
  })).filter((group) => group.items.length);

  return (
    <div className="findings-panel">
      {grouped.map((group) => (
        <section key={group.severity} className="finding-group">
          <header className={`finding-group-head sev-${group.severity}`}>
            <span className="dot" />
            <span>{SEVERITY_LABEL[group.severity as Severity]}</span>
            <span className="finding-group-count">{group.items.length}</span>
          </header>
          <div className="finding-group-items">
            {group.items.map((finding) => (
              <FindingCard key={finding.id} finding={finding} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
