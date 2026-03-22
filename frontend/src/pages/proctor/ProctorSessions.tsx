import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listSessions } from '@/api'

export function ProctorSessions() {
  const [sessions, setSessions] = useState<{ id: number; exam_title: string | null; exam_code: string | null; candidate_identifier: string | null; status: string }[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    const token = sessionStorage.getItem('proctor_token')
    if (!token) {
      window.location.href = '/proctor/login'
      return
    }
    listSessions(token)
      .then((r) => setSessions(r.sessions))
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div style={{ padding: 24 }}>Error: {error}</div>

  return (
    <div style={{ maxWidth: 800, margin: '2rem auto', padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Sessions</h1>
        <button type="button" onClick={() => sessionStorage.removeItem('proctor_token') && (window.location.href = '/proctor/login')}>
          Log out
        </button>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
            <th style={{ padding: 8 }}>ID</th>
            <th style={{ padding: 8 }}>Exam</th>
            <th style={{ padding: 8 }}>Candidate</th>
            <th style={{ padding: 8 }}>Status</th>
            <th style={{ padding: 8 }}></th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((s) => (
            <tr key={s.id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: 8 }}>{s.id}</td>
              <td style={{ padding: 8 }}>{s.exam_title ?? s.exam_code ?? '—'}</td>
              <td style={{ padding: 8 }}>{s.candidate_identifier ?? '—'}</td>
              <td style={{ padding: 8 }}>{s.status}</td>
              <td style={{ padding: 8 }}>
                <Link to={`/proctor/session/${s.id}`}>Watch</Link>
                {' · '}
                <Link to={`/proctor/review/${s.id}`}>Review</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {sessions.length === 0 && <p style={{ marginTop: 16, color: '#666' }}>No sessions yet.</p>}
    </div>
  )
}
