import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { proctorLogin } from '@/api'

export function ProctorLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await proctorLogin(email, password)
      sessionStorage.setItem('proctor_token', data.access_token)
      sessionStorage.setItem('proctor_id', String(data.proctor_id))
      navigate('/proctor/sessions')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '4rem auto', padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>Proctor login</h1>
      <p style={{ color: '#666', marginBottom: 24 }}>Sign in to monitor exams.</p>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>
        {error && <p style={{ color: '#b91c1c', marginBottom: 16 }}>{error}</p>}
        <button type="submit" className="primary" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
