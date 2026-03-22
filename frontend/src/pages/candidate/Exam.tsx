import React, { useEffect, useRef, useCallback, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { JoinResponse } from '@/api'

const WS_URL = (location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + location.host

function useWebRTCAndEvents(sessionId: number, onReady: () => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const localVideoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const onReadyRef = useRef(onReady)
  onReadyRef.current = onReady

  const sendEvent = useCallback((eventType: string, payload?: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event_type: eventType, payload: payload ?? {} }))
    }
  }, [])

  const sendSignaling = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  useEffect(() => {
    let ws: WebSocket
    const wsPath = `/ws/session/${sessionId}?role=candidate`
    ws = new WebSocket(WS_URL + wsPath)
    wsRef.current = ws

    ws.onopen = async () => {
      sendEvent('camera_on')
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        streamRef.current = stream
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream
        }

        const pc = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        })
        pcRef.current = pc
        stream.getTracks().forEach((track) => pc.addTrack(track, stream))

        pc.onicecandidate = (e) => {
          if (e.candidate) sendSignaling({ type: 'webrtc_ice', candidate: e.candidate.toJSON() })
        }

        const offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        sendSignaling({ type: 'webrtc_offer', sdp: offer })
        onReadyRef.current()
      } catch (err) {
        console.error('getUserMedia or createOffer failed', err)
      }
    }

    ws.onmessage = async (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'webrtc_answer' && msg.sdp && pcRef.current) {
          await pcRef.current.setRemoteDescription(new RTCSessionDescription(msg.sdp))
        }
        if (msg.type === 'webrtc_ice' && msg.candidate && pcRef.current) {
          await pcRef.current.addIceCandidate(new RTCIceCandidate(msg.candidate))
        }
      } catch (e) {
        // ignore
      }
    }

    return () => {
      ws.close()
      wsRef.current = null
      pcRef.current?.close()
      pcRef.current = null
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [sessionId, sendEvent, sendSignaling])

  return { sendEvent, localVideoRef }
}

function ExamContent() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const sid = Number(sessionId)
  const [ready, setReady] = useState(false)
  const { sendEvent, localVideoRef } = useWebRTCAndEvents(sid, () => setReady(true))

  useEffect(() => {
    const handleVisibility = () =>
      sendEvent('tab_visibility', { visible: document.visibilityState === 'visible' })
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [sendEvent])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          padding: 8,
          background: '#1a1a1a',
          color: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>Exam in progress</span>
        <button
          type="button"
          className="primary"
          style={{ background: '#444' }}
          onClick={() => {
            sendEvent('camera_off')
            navigate(`/finish/${sid}`)
          }}
        >
          Submit & finish
        </button>
      </div>
      <div style={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#111' }}>
        <video
          ref={localVideoRef}
          autoPlay
          muted
          playsInline
          style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
        />
        {!ready && (
          <div style={{ position: 'absolute', color: '#888' }}>Starting camera…</div>
        )}
      </div>
    </div>
  )
}

export function Exam() {
  const { sessionId } = useParams()
  const [joinData, setJoinData] = useState<JoinResponse | null>(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const raw = sessionStorage.getItem('proctor_join')
    if (!raw) {
      setError('No session. Start from Join.')
      return
    }
    setJoinData(JSON.parse(raw) as JoinResponse)
  }, [sessionId])

  if (error) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <p style={{ color: '#b91c1c' }}>{error}</p>
        <a href="/join">Go to Join</a>
      </div>
    )
  }

  if (!joinData) return <div style={{ padding: 24 }}>Loading…</div>

  return <ExamContent />
}
