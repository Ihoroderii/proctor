/**
 * Entry point for deep links from external apps (e.g. FCE Exam Trainer).
 * Expects at least session_id; optional room_name.
 * Stores join data and redirects to /exam/:sessionId.
 */
import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'

export function Entry() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState('')

  useEffect(() => {
    const sessionId = searchParams.get('session_id')
    const roomName = searchParams.get('room_name')

    if (!sessionId) {
      setError('Missing session_id. Use Join or the link from your exam app.')
      return
    }

    const joinData = {
      session_id: Number(sessionId),
      room_name: roomName ?? `proctor-session-${sessionId}`,
    }
    sessionStorage.setItem('proctor_join', JSON.stringify(joinData))
    navigate(`/exam/${sessionId}`, { replace: true })
  }, [searchParams, navigate])

  if (error) {
    return (
      <div style={{ maxWidth: 400, margin: '4rem auto', padding: 24, textAlign: 'center' }}>
        <p style={{ color: '#b91c1c', marginBottom: 16 }}>{error}</p>
        <a href="/join">Go to Join</a>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 400, margin: '4rem auto', padding: 24, textAlign: 'center' }}>
      <p>Starting proctored exam…</p>
    </div>
  )
}
