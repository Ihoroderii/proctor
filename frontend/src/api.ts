const API = '/api'

export type JoinResponse = {
  session_id: number
  room_name: string
}

export async function joinExam(examCode: string, candidateIdentifier: string): Promise<JoinResponse> {
  const res = await fetch(`${API}/session/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exam_code: examCode, candidate_identifier: candidateIdentifier }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export type ProctorLoginResponse = {
  access_token: string
  token_type: string
  proctor_id: number
  email: string
}

export async function proctorLogin(email: string, password: string): Promise<ProctorLoginResponse> {
  const res = await fetch(`${API}/proctor/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export type SessionSummary = {
  id: number
  room_name: string
  exam_id: number
  exam_title: string | null
  exam_code: string | null
  candidate_identifier: string | null
  status: string
  started_at: string | null
  created_at: string | null
}

export async function listSessions(token: string): Promise<{ sessions: SessionSummary[] }> {
  const res = await fetch(`${API}/proctor/sessions`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to list sessions')
  return res.json()
}

export type SessionDetail = SessionSummary & { ended_at: string | null }

export async function getSession(sessionId: number, token: string): Promise<SessionDetail> {
  const res = await fetch(`${API}/proctor/sessions/${sessionId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to get session')
  return res.json()
}

export async function getReport(sessionId: number, token: string) {
  const res = await fetch(`${API}/proctor/sessions/${sessionId}/report`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to get report')
  return res.json()
}

/** Path + query for WebSocket (use with current host). */
export function wsSessionPath(sessionId: number, role: 'candidate' | 'proctor', proctorToken?: string): string {
  let path = `/ws/session/${sessionId}?role=${role}`
  if (role === 'proctor' && proctorToken) path += `&token=${encodeURIComponent(proctorToken)}`
  return path
}
