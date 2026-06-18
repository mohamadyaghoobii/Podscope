export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type Finding = {
  rule_id: string;
  title: string;
  severity: Severity;
  target: string;
  namespace?: string | null;
  resource_kind?: string | null;
  resource_name?: string | null;
  message: string;
  remediation: string;
  patch_hint?: string | null;
  references: string[];
};

export type SeverityCounts = Record<Severity, number>;

export type AnalysisResult = {
  name: string;
  score: number;
  status: "pass" | "review" | "fail";
  resource_count: number;
  workload_count: number;
  namespace_count: number;
  severity_counts: SeverityCounts;
  resources: Array<{ kind: string; name: string; namespace?: string | null; containers: string[] }>;
  findings: Finding[];
  notes: string[];
};

export type ExampleManifest = {
  name: string;
  description: string;
  content: string;
};

export type RuleInfo = {
  rule_id: string;
  title: string;
  default_severity: Severity;
  category: string;
  description: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export async function getExamples(): Promise<ExampleManifest[]> {
  return getJson<ExampleManifest[]>("/api/examples");
}

export async function getRules(): Promise<RuleInfo[]> {
  return getJson<RuleInfo[]>("/api/rules");
}

export async function analyzeManifest(name: string, content: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, content })
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail || payload);
    throw new Error(detail || `Analysis failed with status ${response.status}`);
  }
  return response.json();
}
