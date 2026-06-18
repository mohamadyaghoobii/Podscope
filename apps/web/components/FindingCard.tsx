"use client";

import { useState } from "react";
import { Finding } from "../lib/api";
import { SeverityBadge } from "./SeverityBadge";
import { CopyButton } from "./CopyButton";

export function FindingCard({ finding }: { finding: Finding }) {
  const [open, setOpen] = useState(false);

  return (
    <article className={`finding-card sev-border-${finding.severity}`}>
      <button className="finding-head" onClick={() => setOpen((value) => !value)} aria-expanded={open}>
        <div className="finding-head-main">
          <div className="finding-title-row">
            <SeverityBadge severity={finding.severity} />
            <span className="finding-rule">{finding.rule_id}</span>
            <span className="finding-confidence">{finding.confidence} confidence</span>
          </div>
          <div className="finding-title">{finding.title}</div>
          <div className="finding-target">
            <span className="chip-kind">{finding.resource_kind}</span>
            <span>{finding.resource_name}</span>
            {finding.namespace && <span className="finding-ns">ns: {finding.namespace}</span>}
          </div>
        </div>
        <span className={`chevron ${open ? "open" : ""}`} aria-hidden="true">›</span>
      </button>

      {open && (
        <div className="finding-body">
          <p className="finding-desc">{finding.description}</p>
          <div className="finding-grid">
            <div>
              <span className="finding-label">Impact</span>
              <p>{finding.impact}</p>
            </div>
            <div>
              <span className="finding-label">Remediation</span>
              <p>{finding.remediation}</p>
            </div>
          </div>
          {finding.path && (
            <div className="finding-path">
              <span className="finding-label">Field</span>
              <code>{finding.path}</code>
              {finding.evidence && <span className="finding-evidence">{finding.evidence}</span>}
            </div>
          )}
          {finding.fixed_example && (
            <div className="finding-fix">
              <div className="finding-fix-head">
                <span className="finding-label">Suggested fix</span>
                <CopyButton text={finding.fixed_example} />
              </div>
              <pre>{finding.fixed_example}</pre>
            </div>
          )}
          {finding.references.length > 0 && (
            <div className="finding-refs">
              {finding.references.map((ref) => (
                <a key={ref} href={ref} target="_blank" rel="noreferrer">
                  Reference
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </article>
  );
}
