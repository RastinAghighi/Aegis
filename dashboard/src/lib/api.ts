/**
 * Aegis API client.
 *
 * Talks to the FastAPI backend (default http://localhost:8000). When backend
 * isn't running yet, pages fall back to mock data — see `mockFindings`.
 */

export const API_URL =
  (import.meta.env.VITE_AEGIS_API_URL as string | undefined) || 'http://localhost:8000';

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface CFRCitation {
  section: string;
  title: string;
  text: string;
  url?: string;
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
}

async function request<T>(path: string): Promise<T> {
  const r = await fetch(`${API_URL}${path}`);
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}

export async function listFindings(): Promise<Finding[]> {
  try {
    return await request<Finding[]>('/findings');
  } catch {
    return mockFindings;
  }
}

export async function listReports(): Promise<Report[]> {
  try {
    return await request<Report[]>('/reports');
  } catch {
    return mockReports;
  }
}

export const mockFindings: Finding[] = [
  {
    id: 'f-001',
    rule_id: 'AC-1',
    rule_title: 'Access Control — auth required',
    severity: 'CRITICAL',
    cfr: {
      section: '164.312(a)(1)',
      title: 'Access control',
      text: 'Implement technical policies and procedures for electronic information systems that maintain electronic protected health information to allow access only to those persons or software programs that have been granted access rights.',
    },
    evidence: {
      file: 'demo/patient-portal/routes/patients.js',
      line_start: 25,
      line_end: 29,
      snippet: "router.get('/:id', async (req, res) => { const patient = await Patient.findByPk(req.params.id); ... })",
      why: 'GET /patients/:id has no authentication middleware in its handler chain.',
    },
    remediation: 'Bind requireAuth before the handler: router.get(\'/:id\', requireAuth, ...)',
    detected_at: '2026-05-15T12:00:00Z',
  },
  {
    id: 'f-002',
    rule_id: 'AC-2',
    rule_title: 'Session Timeout',
    severity: 'HIGH',
    cfr: {
      section: '164.312(a)(2)(iii)',
      title: 'Automatic logoff',
      text: 'Implement electronic procedures that terminate an electronic session after a predetermined time of inactivity.',
    },
    evidence: {
      file: 'demo/patient-portal/middleware/session.js',
      line_start: 9,
      line_end: 9,
      snippet: 'maxAge: 86400000',
      why: 'Session cookie lifetime is 24h; HIPAA guidance recommends ≤15min idle timeout for PHI workstations.',
    },
    remediation: 'Set maxAge to 900000 (15 minutes) and reset on each authenticated request.',
    detected_at: '2026-05-15T12:00:00Z',
  },
  {
    id: 'f-003',
    rule_id: 'EN-1',
    rule_title: 'Encryption at Rest',
    severity: 'CRITICAL',
    cfr: {
      section: '164.312(a)(2)(iv)',
      title: 'Encryption and decryption',
      text: 'Implement a mechanism to encrypt and decrypt electronic protected health information.',
    },
    evidence: {
      file: 'demo/patient-portal/models/Patient.js',
      line_start: 22,
      line_end: 25,
      snippet: 'ssn: { type: DataTypes.STRING, allowNull: false }',
      why: 'SSN column stored as plaintext STRING — no application or column-level encryption.',
    },
    remediation: 'Encrypt SSN at rest using pgcrypto or a Sequelize hook with KMS-backed key wrapping.',
    detected_at: '2026-05-15T12:00:00Z',
  },
];

export const mockReports: Report[] = [
  {
    id: 'r-001',
    target: 'demo/patient-portal',
    generated_at: '2026-05-15T12:00:00Z',
    findings: mockFindings,
  },
];

export function severityColor(s: Severity): string {
  switch (s) {
    case 'CRITICAL':
      return 'bg-red-600 text-white';
    case 'HIGH':
      return 'bg-orange-500 text-white';
    case 'MEDIUM':
      return 'bg-yellow-500 text-black';
    case 'LOW':
      return 'bg-slate-400 text-white';
  }
}
