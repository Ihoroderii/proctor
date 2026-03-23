import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getSession, wsSessionPath } from '@/api'

const WS_URL = (location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + location.host

export function ProctorSession() {
  const { sessionId } = useParams()
  const [session, setSession] = useState<{
    candidate_identifier: string | null
    exam_title: string | null
  } | null>(null)
  const [flags, setFlags] = useState<
    { rule_id: string; severity: string; message: string; raised_at: string }[]
  >([])
  const [streamReady, setStreamReady] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null)
  const proctorToken = sessionStorage.getItem('proctor_token')

  useEffect(() => {
    if (!sessionId || !proctorToken) return
    const id = Number(sessionId)
    getSession(id, proctorToken).then(setSession)
  }, [sessionId, proctorToken])

  useEffect(() => {
    if (!sessionId || !proctorToken) return
    const id = Number(sessionId)
    const path = wsSessionPath(id, 'proctor', proctorToken)
    const ws = new WebSocket(WS_URL + path)
    wsRef.current = ws

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'flag') {
          setFlags((f) => [...f, msg.flag])
          return
        }
        // WebRTC signaling: offer from candidate
        if (msg.type === 'webrtc_offer' && msg.sdp) {
          handleOffer(msg.sdp)
          return
        }
        if (msg.type === 'webrtc_ice' && msg.candidate && pcRef.current) {
          pcRef.current.addIceCandidate(new RTCIceCandidate(msg.candidate)).catch(() => {})
        }
      } catch {}
    }

    async function handleOffer(sdp: RTCSessionDescriptionInit) {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      })
      pcRef.current = pc

      pc.ontrack = (e) => {
        if (remoteVideoRef.current && e.streams[0]) {
          remoteVideoRef.current.srcObject = e.streams[0]
          setStreamReady(true)
        }
      }
      pc.onicecandidate = (e) => {
        if (e.candidate && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'webrtc_ice', candidate: e.candidate.toJSON() }))
        }
      }

      await pc.setRemoteDescription(new RTCSessionDescription(sdp))
      const answer = await pc.createAnswer()
      await pc.setLocalDescription(answer)
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'webrtc_answer', sdp: answer }))
      }
    }

    return () => {
      ws.close()
      wsRef.current = null
      pcRef.current?.close()
      pcRef.current = null
    }
  }, [sessionId, proctorToken])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header
        style={{
          padding: 8,
          background: '#1a1a1a',
          color: '#fff',
          display: 'flex',
          gap: 16,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <Link to="/proctor/sessions" style={{ color: '#fff' }}>
          ← Sessions
        </Link>
        <span>
          Session {sessionId} · {session?.candidate_identifier ?? '—'} · {session?.exam_title ?? '—'}
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button type="button" className="primary" style={{ background: '#b45309' }}>
            Warn
          </button>
          <button type="button" className="primary" style={{ background: '#444' }}>
            Pause
          </button>
          <button type="button" className="primary" style={{ background: '#b91c1c' }}>
            Terminate
          </button>
        </div>
      </header>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <div style={{ flex: 1, minWidth: 0, background: '#111', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
          />
          {!streamReady && (
            <div style={{ position: 'absolute', color: '#888' }}>
              Waiting for candidate camera…
            </div>
          )}
        </div>
        <aside style={{ width: 280, borderLeft: '1px solid #eee', padding: 16, overflow: 'auto' }}>
          <h3 style={{ marginBottom: 8 }}>Flags</h3>
          {flags.length === 0 && (
            <p style={{ color: '#666', fontSize: 14 }}>No flags yet.</p>
          )}
          {flags.map((f, i) => (
            <div
              key={i}
              style={{
                padding: 8,
                marginBottom: 8,
                background: '#fef2f2',
                borderRadius: 8,
                fontSize: 14,
              }}
            >
              <span style={{ fontWeight: 600, color: '#b91c1c' }}>{f.severity}</span>
              <p style={{ margin: '4px 0 0' }}>{f.message}</p>
              <time style={{ fontSize: 12, color: '#666' }}>{f.raised_at}</time>
            </div>
          ))}
        </aside>
      </div>
    </div>
  )
}
