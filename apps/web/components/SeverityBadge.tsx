import { Severity } from "../lib/api";
import { SEVERITY_LABEL } from "../lib/format";

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`badge badge-${severity}`}>{SEVERITY_LABEL[severity]}</span>;
}
