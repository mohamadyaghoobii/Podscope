import { AnalysisResult, Severity } from "../lib/api";
import { SEVERITY_LABEL, SEVERITY_ORDER } from "../lib/format";

export function StatTiles({ result }: { result: AnalysisResult }) {
  const tiles = [
    { label: "Resources", value: result.resource_count },
    { label: "Workloads", value: result.workload_count },
    { label: "Namespaces", value: result.namespace_count },
    { label: "Findings", value: result.findings.length }
  ];
  return (
    <div className="stat-tiles">
      {tiles.map((tile) => (
        <div className="stat-tile" key={tile.label}>
          <strong>{tile.value}</strong>
          <span>{tile.label}</span>
        </div>
      ))}
    </div>
  );
}

export function SeverityBreakdown({
  counts,
  active,
  onSelect
}: {
  counts: Record<Severity, number>;
  active: Severity | "all";
  onSelect: (value: Severity | "all") => void;
}) {
  return (
    <div className="severity-breakdown">
      {SEVERITY_ORDER.map((severity) => {
        const count = counts[severity];
        const isActive = active === severity;
        return (
          <button
            key={severity}
            className={`severity-cell sev-${severity} ${isActive ? "is-active" : ""} ${count ? "" : "is-empty"}`}
            onClick={() => onSelect(isActive ? "all" : severity)}
            disabled={!count}
          >
            <span className="dot" />
            <strong>{count}</strong>
            <span className="severity-name">{SEVERITY_LABEL[severity]}</span>
          </button>
        );
      })}
    </div>
  );
}

export function CategoryBreakdown({ result }: { result: AnalysisResult }) {
  if (!result.category_counts.length) {
    return null;
  }
  const max = Math.max(...result.category_counts.map((item) => item.count), 1);
  return (
    <div className="category-breakdown">
      {result.category_counts.map((item) => (
        <div className="category-row" key={item.category}>
          <span className="category-name">{item.category}</span>
          <div className="category-track">
            <div className="category-fill" style={{ width: `${(item.count / max) * 100}%` }} />
          </div>
          <span className="category-count">{item.count}</span>
        </div>
      ))}
    </div>
  );
}
