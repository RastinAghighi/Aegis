/**
 * Aegis API client. Talks to the FastAPI backend.
 * Base URL via VITE_API_URL, defaults to http://localhost:8000.
 */

export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000';

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface CFRCitation {
  section: string;
  title: string;
  text: string;
  url?: string | null;
}

export interface Evidence {
  file: string;
  line_start: number;
  line_end: number;
  snippet: string;
  why: string;
}

export interface Finding {
  id: string;
  rule_id: string;
  rule_title: string;
  severity: Severity;
  cfr: CFRCitation;
  evidence: Evidence;
  remediation: string;
  detected_at: string;
}

export interface Report {
  id: string;
  target: string;
  generated_at: string;
  findings: Finding[];
  risk_score: number;
  counts_by_severity: Record<Severity, number>;
}

export interface Rule {
  rule_id: string;
  title: string;
  cfr_section: string;
  severity: Severity;
  description: string;
}

export interface HealthResponse {
  status: string;
  scan_target: string;
  last_scan: string | null;
  findings_cached: number;
}

export interface FlowNode {
  id: string;
  label: string;
  sublabel: string;
  file: string | null;
  line: number | null;
  type: 'schema' | 'route' | 'error_handler' | 'sink';
}

export interface FlowEdge {
  from: string;
  to: string;
  label: string;
}

export interface FlowGraph {
  title: string;
  cfr_citation: string;
  severity: Severity;
  description: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
}

export class APIError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, init);
  if (!r.ok) {
    let detail = `${r.status}`;
    try {
      const body = await r.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new APIError(r.status, detail);
  }
  return r.json();
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health', { signal });
}

export function getFindings(): Promise<Report> {
  return request<Report>('/api/findings');
}

export function getFinding(id: string): Promise<Finding> {
  return request<Finding>(`/api/findings/${id}`);
}

export function getRules(): Promise<Rule[]> {
  return request<Rule[]>('/api/rules');
}

export function runScan(): Promise<Report> {
  return request<Report>('/api/scan', { method: 'POST' });
}

export function getFlowGraph(): Promise<FlowGraph> {
  return request<FlowGraph>('/api/flow-graph');
}

export const SEVERITY_ORDER: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export const SEVERITY_HEX: Record<Severity, string> = {
  CRITICAL: '#e11d48', // rose-600
  HIGH: '#d97706', // amber-600
  MEDIUM: '#eab308', // yellow-500
  LOW: '#3b82f6', // blue-500
};

export function severityBadgeClass(s: Severity): string {
  switch (s) {
    case 'CRITICAL':
      return 'bg-rose-600 text-white hover:bg-rose-600/90';
    case 'HIGH':
      return 'bg-amber-600 text-white hover:bg-amber-600/90';
    case 'MEDIUM':
      return 'bg-yellow-500 text-slate-950 hover:bg-yellow-500/90';
    case 'LOW':
      return 'bg-blue-500 text-white hover:bg-blue-500/90';
  }
}

// Back-compat — some pages may import this name.
export const severityColor = severityBadgeClass;
