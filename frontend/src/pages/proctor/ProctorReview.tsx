import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport } from '@/api'

export function ProctorReview() {
  const { sessionId } = useParams()
  const [report, setReport] = useState<{
    session_id: number
    exam_title: string | null
    candidate_identifier: string | null
    status: string
    started_at: string | null
    ended_at: string | null
    events: { event_type: string; source: string; created_at: string | null }[]
    flags: { severity: string; rule_id: string; message: string; raised_at: string | null }[]
    recordings: { id: number; file_url: string | null }[]
    proctor_notes: { note: string; timestamp_sec: number | null }[]
  } | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = sessionStorage.getItem('proctor_token')
    if (!token || !sessionId) {
      if (!token) window.location.href = '/proctor/login'
      return
    }
    getReport(Number(sessionId), token).then(setReport).catch((e) => setError(e.message))
  }, [sessionId])

  if (error) return <div style={{ padding: 24 }}>Error: {error}</div>
  if (!report) return <div style={{ padding: 24 }}>Loading…</div>

  return (
    <div style={{ maxWidth: 900, margin: '2rem auto', padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Review · Session {report.session_id}</h1>
        <Link to="/proctor/sessions">← Sessions</Link>
      </div>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Summary</h2>
        <p>Exam: {report.exam_title ?? '—'}</p>
        <p>Candidate: {report.candidate_identifier ?? '—'}</p>
        <p>Status: {report.status}</p>
        <p>Started: {report.started_at ?? '—'}</p>
        <p>Ended: {report.ended_at ?? '—'}</p>
      </section>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Flags ({report.flags.length})</h2>
        {report.flags.length === 0 && <p style={{ color: '#666' }}>No flags.</p>}
        <ul style={{ listStyle: 'none' }}>
          {report.flags.map((f, i) => (
            <li key={i} style={{ padding: 8, marginBottom: 4, background: '#f5f5f5', borderRadius: 8 }}>
              <strong>{f.severity}</strong> · {f.message} · {f.raised_at ?? ''}
            </li>
          ))}
        </ul>
      </section>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Recordings</h2>
        {report.recordings.length === 0 && <p style={{ color: '#666' }}>No recordings.</p>}
        {report.recordings.map((r) => (
          <p key={r.id}>
            {r.file_url ? <a href={r.file_url} target="_blank" rel="noreferrer">Recording #{r.id}</a> : `Recording #${r.id} (pending)`}
          </p>
        ))}
      </section>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Proctor notes ({report.proctor_notes.length})</h2>
        {report.proctor_notes.length === 0 && <p style={{ color: '#666' }}>No notes.</p>}
        <ul style={{ listStyle: 'none' }}>
          {report.proctor_notes.map((n, i) => (
            <li key={i} style={{ padding: 8, marginBottom: 4, background: '#f0f9ff', borderRadius: 8 }}>
              {n.note} {n.timestamp_sec != null && <span style={{ color: '#666' }}>(@{n.timestamp_sec}s)</span>}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
