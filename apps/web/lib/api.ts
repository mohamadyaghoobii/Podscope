export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Confidence = "high" | "medium" | "low";
export type FindingStatus = "fail" | "warn" | "pass" | "info";
export type RunStatus = "pass" | "review" | "fail";

export type Finding = {
  id: string;
  rule_id: string;
  title: string;
  severity: Severity;
  status: FindingStatus;
  category: string;
  confidence: Confidence;
  resource_kind: string;
  resource_name: string;
  namespace?: string | null;
  path?: string | null;
  description: string;
  impact: string;
  remediation: string;
  fixed_example?: string | null;
  evidence?: string | null;
  references: string[];
};

export type SeverityCounts = Record<Severity, number>;

export type ResourceSummary = {
  kind: string;
  name: string;
  namespace?: string | null;
  containers: string[];
  images: string[];
  finding_count: number;
  top_severity?: Severity | null;
};

export type Scorecard = {
  score: number;
  grade: string;
  status: RunStatus;
  explanation: string;
  checks_run: number;
  checks_passed: number;
  checks_failed: number;
};

export type AnalysisResult = {
  meta: {
    schema_version: string;
    name: string;
    project?: string | null;
    environment?: string | null;
    strict: boolean;
    generated_at: string;
  };
  scorecard: Scorecard;
  summary: string;
  resource_count: number;
  workload_count: number;
  namespace_count: number;
  severity_counts: SeverityCounts;
  category_counts: Array<{ category: string; count: number }>;
  resources: ResourceSummary[];
  findings: Finding[];
  next_steps: string[];
  notes: string[];
};

export type ExampleManifest = {
  name: string;
  title: string;
  description: string;
  intent: "risky" | "hardened" | "reference";
  content: string;
};

export type RuleInfo = {
  id: string;
  title: string;
  severity: Severity;
  category: string;
  confidence: Confidence;
  description: string;
  impact: string;
  remediation: string;
  references: string[];
};

export type AiSummary = {
  provider: string;
  ai_enabled: boolean;
  headline: string;
  executive_summary: string;
  readiness: string;
  prioritized_fixes: string[];
};

export type AnalyzeOptions = {
  strict?: boolean;
  categories?: string[] | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = payload?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return response.json();
}

export function getExamples(): Promise<ExampleManifest[]> {
  return getJson<ExampleManifest[]>("/api/examples");
}

export function getRules(): Promise<RuleInfo[]> {
  return getJson<RuleInfo[]>("/api/rules");
}

export function analyzeManifest(
  name: string,
  content: string,
  options?: AnalyzeOptions,
  environment?: string
): Promise<AnalysisResult> {
  return postJson<AnalysisResult>("/api/analyze", {
    name,
    content,
    environment,
    options: { strict: options?.strict ?? false, categories: options?.categories ?? null }
  });
}

export function summarizeManifest(name: string, content: string): Promise<AiSummary> {
  return postJson<AiSummary>("/api/ai/summarize", { name, content, audience: "platform" });
}
