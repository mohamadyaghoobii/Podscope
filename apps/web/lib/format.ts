import { RunStatus, Severity } from "./api";

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  info: "Info"
};

export const STATUS_LABEL: Record<RunStatus, string> = {
  pass: "Deployable",
  review: "Needs review",
  fail: "Blocked"
};

export const CATEGORIES = [
  "Workload Security",
  "RBAC",
  "Network Exposure",
  "Secrets",
  "Reliability",
  "Hygiene"
];

export function gradeTone(grade: string): "good" | "warn" | "bad" {
  if (grade === "A" || grade === "B") return "good";
  if (grade === "C" || grade === "D") return "warn";
  return "bad";
}
