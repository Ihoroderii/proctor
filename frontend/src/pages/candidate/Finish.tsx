import { useParams, Link } from 'react-router-dom'

export function Finish() {
  const { sessionId } = useParams()

  return (
    <div style={{ maxWidth: 480, margin: '4rem auto', padding: 24, textAlign: 'center' }}>
      <h1 style={{ marginBottom: 8 }}>Exam submitted</h1>
      <p style={{ color: '#666', marginBottom: 24 }}>
        Your session has been submitted. You may close this tab.
      </p>
      <p style={{ fontSize: 14, color: '#888' }}>Session ID: {sessionId}</p>
      <Link to="/join" style={{ display: 'inline-block', marginTop: 24 }}>Join another exam</Link>
    </div>
  )
}
