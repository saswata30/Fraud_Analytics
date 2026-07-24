async function jget<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
async function jpost<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export interface Meta {
  catalog: string;
  schema: string;
  llm: string;
  stack: string[];
}

export interface Kpi {
  total_claims: number;
  fraud_claims: number;
  fraud_rate: number;
  fraud_payout: number;
  total_payout: number;
  high_risk_claims: number;
  avg_claim: number;
}
export interface TrendPoint {
  month: string;
  claims: number;
  fraud_claims: number;
  fraud_rate: number;
  fraud_payout: number;
}
export interface RegionRow {
  region: string;
  claims: number;
  fraud_claims: number;
  fraud_rate: number;
  fraud_payout: number;
}
export interface PolicyRow {
  policy_type: string;
  claims: number;
  fraud_claims: number;
  fraud_rate: number;
}
export interface RiskBucket {
  score: number;
  total: number;
  fraud: number;
  legit: number;
}
export interface Dashboard {
  kpi: Kpi;
  trend: TrendPoint[];
  by_region: RegionRow[];
  by_policy: PolicyRow[];
  risk_dist: RiskBucket[];
}

export interface Claim {
  claim_id: string;
  policyholder_id: string;
  policy_type: string;
  claim_type: string;
  region: string;
  channel: string;
  claim_date: string;
  claim_amount: number;
  report_lag_days: number;
  fraud_risk_score: number;
  claim_status: string;
  is_fraud: number;
}

export interface ChartSpec {
  type: "line" | "bar";
  x: string;
  series: string[];
  data: Record<string, any>[];
}
export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  columns: string[];
  rows: any[][];
  chart: ChartSpec | null;
  error: string | null;
}

export interface UploadResponse {
  filename: string;
  volume_path: string;
  chars: number;
  preview: string;
  text: string;
}

export const api = {
  meta: () => jget<Meta>("/api/meta"),
  dashboard: () => jget<Dashboard>("/api/dashboard"),
  highRisk: (limit = 25) => jget<Claim[]>(`/api/high-risk?limit=${limit}`),
  ucLink: (object = "") => jget<{ url: string }>(`/api/uc-link?object=${encodeURIComponent(object)}`),
  chat: (body: { question: string; conversation_id?: string | null; doc_context?: string }) =>
    jpost<ChatResponse>("/api/chat", body),
  upload: async (file: File): Promise<UploadResponse> => {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch("/api/upload", { method: "POST", body: fd });
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    return r.json();
  },
};

export function fmtGbp(n: number): string {
  if (!n) return "£0";
  if (n >= 1e9) return `£${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `£${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `£${(n / 1e3).toFixed(0)}K`;
  return `£${n.toFixed(0)}`;
}
export function fmtPct(n: number, dp = 1): string {
  return `${(n * 100).toFixed(dp)}%`;
}
export function fmtNum(n: number): string {
  return n.toLocaleString("en-GB");
}
