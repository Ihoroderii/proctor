import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { joinExam } from '@/api'

export function Join() {
  const [searchParams] = useSearchParams()
  const [examCode, setExamCode] = useState('')
  const [name, setName] = useState('')
  useEffect(() => {
    const code = searchParams.get('exam_code')
    const n = searchParams.get('name')
    if (code) setExamCode(code)
    if (n) setName(n)
  }, [searchParams])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!examCode.trim() || !name.trim()) {
      setError('Enter exam code and your name')
      return
    }
    setLoading(true)
    try {
      const data = await joinExam(examCode.trim(), name.trim())
      sessionStorage.setItem('proctor_join', JSON.stringify(data))
      navigate(`/exam/${data.session_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Join failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '4rem auto', padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>Join exam</h1>
      <p style={{ color: '#666', marginBottom: 24 }}>
        Enter the exam code and your name. Your webcam and optional screen will be recorded.
      </p>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Exam code</label>
          <input
            value={examCode}
            onChange={(e) => setExamCode(e.target.value)}
            placeholder="e.g. MATH101"
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Your name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Full name"
            style={{ width: '100%' }}
          />
        </div>
        {error && <p style={{ color: '#b91c1c', marginBottom: 16 }}>{error}</p>}
        <button type="submit" className="primary" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Joining…' : 'Continue'}
        </button>
      </form>
      <p style={{ marginTop: 24, fontSize: 14, color: '#666' }}>
        By continuing you consent to being recorded during the exam.
      </p>
    </div>
  )
}
