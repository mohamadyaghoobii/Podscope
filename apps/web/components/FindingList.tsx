import { Finding } from "../lib/api";
import { SeverityBadge } from "./SeverityBadge";

export function FindingList({ findings }: { findings: Finding[] }) {
  if (!findings.length) {
    return <div className="empty-state">No baseline findings were detected in this manifest bundle.</div>;
  }

  return (
    <div className="finding-list">
      {findings.map((finding, index) => (
        <article className="finding-card" key={`${finding.rule_id}-${finding.target}-${index}`}>
          <div className="finding-head">
            <div>
              <div className="finding-title">{finding.title}</div>
              <div className="finding-target">{finding.target}</div>
            </div>
            <SeverityBadge severity={finding.severity} />
          </div>
          <p>{finding.message}</p>
          <div className="finding-remediation">{finding.remediation}</div>
          {finding.patch_hint ? <pre>{finding.patch_hint}</pre> : null}
        </article>
      ))}
    </div>
  );
}
