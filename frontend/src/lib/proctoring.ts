/**
 * Browser-based proctoring: face detection, phone detection, voice activity,
 * tab/fullscreen/window monitoring. All detection runs client-side.
 *
 * Face detection uses TensorFlow.js BlazeFace.
 * Phone detection uses TensorFlow.js COCO-SSD (detects "cell phone" class).
 * Voice detection uses Web Audio API.
 * Browser lockdown uses native Page Visibility, Fullscreen, and focus APIs.
 */

// ─── Types ────────────────────────────────────────────────────────────────

export type ProctoringEvent = {
  event_type: string
  payload?: Record<string, unknown>
}

export type EventCallback = (event: ProctoringEvent) => void

export interface ProctoringConfig {
  /** Interval between face/phone detection frames (ms). Default: 1500 */
  detectionIntervalMs?: number
  /** Voice detection threshold (0-1). Default: 0.02 */
  voiceThreshold?: number
  /** Require fullscreen? Default: true */
  enforceFullscreen?: boolean
  /** Enable phone detection (loads ~5MB model)? Default: true */
  enablePhoneDetection?: boolean
}

// ─── State ────────────────────────────────────────────────────────────────

let running = false
let onEvent: EventCallback = () => {}
let detectionInterval: ReturnType<typeof setInterval> | null = null
let voiceInterval: ReturnType<typeof setInterval> | null = null
let audioCtx: AudioContext | null = null
let analyser: AnalyserNode | null = null
let faceModel: any = null
let cocoModel: any = null
let videoEl: HTMLVideoElement | null = null
let canvasEl: HTMLCanvasElement | null = null

// Last known states for edge-triggered events
let lastFacePresent = true
let lastMultipleFaces = false
let lastPhonePresent = false
let lastVoiceActive = false

// ─── Model Loading ────────────────────────────────────────────────────────

async function loadBlazeFace(): Promise<any> {
  // Dynamic import — bundled by Vite when installed
  const blazeface = await import('@tensorflow-models/blazeface')
  // BlazeFace needs tf.js core
  await import('@tensorflow/tfjs-core')
  await import('@tensorflow/tfjs-backend-webgl')
  return blazeface.load()
}

async function loadCocoSsd(): Promise<any> {
  const cocoSsd = await import('@tensorflow-models/coco-ssd')
  return cocoSsd.load()
}

// ─── Detection Functions ──────────────────────────────────────────────────

function getCanvas(): HTMLCanvasElement {
  if (!canvasEl) {
    canvasEl = document.createElement('canvas')
  }
  return canvasEl
}

async function detectFaces(): Promise<{ count: number }> {
  if (!faceModel || !videoEl || videoEl.readyState < 2) return { count: 0 }
  try {
    const predictions = await faceModel.estimateFaces(videoEl, false)
    return { count: predictions.length }
  } catch {
    return { count: 0 }
  }
}

async function detectPhone(): Promise<boolean> {
  if (!cocoModel || !videoEl || videoEl.readyState < 2) return false
  try {
    const predictions = await cocoModel.detect(videoEl)
    return predictions.some(
      (p: any) => p.class === 'cell phone' && p.score > 0.5
    )
  } catch {
    return false
  }
}

function checkVoice(threshold: number): boolean {
  if (!analyser) return false
  const data = new Uint8Array(analyser.fftSize)
  analyser.getByteTimeDomainData(data)
  // Calculate RMS
  let sum = 0
  for (let i = 0; i < data.length; i++) {
    const val = (data[i] - 128) / 128
    sum += val * val
  }
  const rms = Math.sqrt(sum / data.length)
  return rms > threshold
}

// ─── Browser Lockdown ─────────────────────────────────────────────────────

function handleVisibilityChange() {
  if (!running) return
  const visible = document.visibilityState === 'visible'
  onEvent({
    event_type: 'tab_visibility',
    payload: { visible },
  })
}

function handleFullscreenChange() {
  if (!running) return
  if (document.fullscreenElement) {
    onEvent({ event_type: 'fullscreen_enter' })
  } else {
    onEvent({ event_type: 'fullscreen_exit' })
  }
}

function handleWindowBlur() {
  if (!running) return
  onEvent({ event_type: 'window_blur' })
}

function handleWindowFocus() {
  if (!running) return
  onEvent({ event_type: 'window_focus' })
}

function handleBeforeUnload(e: BeforeUnloadEvent) {
  if (!running) return
  e.preventDefault()
  e.returnValue = 'Exam in progress. Are you sure you want to leave?'
}

// Prevent common shortcuts (Ctrl+Tab, Alt+Tab can't be blocked, but we detect them via blur)
function handleKeydown(e: KeyboardEvent) {
  if (!running) return
  // Block Ctrl+W, Ctrl+T, Ctrl+N, F5
  if (
    (e.ctrlKey && ['w', 't', 'n'].includes(e.key.toLowerCase())) ||
    e.key === 'F5'
  ) {
    e.preventDefault()
    e.stopPropagation()
  }
}

// ─── Public API ───────────────────────────────────────────────────────────

/**
 * Start all proctoring detection. Call after getUserMedia succeeds.
 * @param stream - The MediaStream from getUserMedia (video + audio)
 * @param video - The video element showing the stream
 * @param callback - Called for each detected event
 * @param config - Optional configuration
 */
export async function startProctoring(
  stream: MediaStream,
  video: HTMLVideoElement,
  callback: EventCallback,
  config: ProctoringConfig = {},
): Promise<void> {
  if (running) return
  running = true
  onEvent = callback
  videoEl = video

  const {
    detectionIntervalMs = 1500,
    voiceThreshold = 0.02,
    enforceFullscreen = true,
    enablePhoneDetection = true,
  } = config

  // ── Load ML models ──
  try {
    faceModel = await loadBlazeFace()
  } catch (err) {
    console.warn('BlazeFace load failed; face detection disabled', err)
  }

  if (enablePhoneDetection) {
    try {
      cocoModel = await loadCocoSsd()
    } catch (err) {
      console.warn('COCO-SSD load failed; phone detection disabled', err)
    }
  }

  // ── Voice detection via Web Audio API ──
  const audioTrack = stream.getAudioTracks()[0]
  if (audioTrack) {
    try {
      audioCtx = new AudioContext()
      const source = audioCtx.createMediaStreamSource(stream)
      analyser = audioCtx.createAnalyser()
      analyser.fftSize = 512
      source.connect(analyser)
      // Don't connect to destination (no feedback)
    } catch (err) {
      console.warn('Audio context failed', err)
    }
  }

  // ── Periodic face + phone detection ──
  detectionInterval = setInterval(async () => {
    if (!running) return

    // Face detection
    const { count } = await detectFaces()
    const facePresent = count >= 1
    const multipleFaces = count >= 2

    if (facePresent && !lastFacePresent) {
      onEvent({ event_type: 'face_detected', payload: { face_count: count } })
    } else if (!facePresent && lastFacePresent) {
      onEvent({ event_type: 'face_missing' })
    }
    lastFacePresent = facePresent

    if (multipleFaces && !lastMultipleFaces) {
      onEvent({ event_type: 'multiple_faces', payload: { face_count: count } })
    }
    lastMultipleFaces = multipleFaces

    // Phone detection
    if (cocoModel) {
      const phoneFound = await detectPhone()
      if (phoneFound && !lastPhonePresent) {
        onEvent({ event_type: 'phone_detected' })
      } else if (!phoneFound && lastPhonePresent) {
        onEvent({ event_type: 'phone_gone' })
      }
      lastPhonePresent = phoneFound
    }
  }, detectionIntervalMs)

  // ── Voice activity detection ──
  voiceInterval = setInterval(() => {
    if (!running || !analyser) return
    const active = checkVoice(voiceThreshold)
    if (active && !lastVoiceActive) {
      onEvent({ event_type: 'voice_detected' })
    } else if (!active && lastVoiceActive) {
      onEvent({ event_type: 'voice_silent' })
    }
    lastVoiceActive = active
  }, 500)

  // ── Browser lockdown listeners ──
  document.addEventListener('visibilitychange', handleVisibilityChange)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  window.addEventListener('blur', handleWindowBlur)
  window.addEventListener('focus', handleWindowFocus)
  window.addEventListener('beforeunload', handleBeforeUnload)
  document.addEventListener('keydown', handleKeydown, true)

  // ── Request fullscreen ──
  if (enforceFullscreen) {
    try {
      await document.documentElement.requestFullscreen()
    } catch {
      // User may deny — we still detect exit
    }
  }
}

/**
 * Stop all proctoring detection and clean up resources.
 */
export function stopProctoring(): void {
  running = false
  onEvent = () => {}

  if (detectionInterval) {
    clearInterval(detectionInterval)
    detectionInterval = null
  }
  if (voiceInterval) {
    clearInterval(voiceInterval)
    voiceInterval = null
  }
  if (audioCtx) {
    audioCtx.close().catch(() => {})
    audioCtx = null
    analyser = null
  }

  faceModel = null
  cocoModel = null
  videoEl = null
  canvasEl = null

  // Reset states
  lastFacePresent = true
  lastMultipleFaces = false
  lastPhonePresent = false
  lastVoiceActive = false

  // Remove listeners
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('blur', handleWindowBlur)
  window.removeEventListener('focus', handleWindowFocus)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  document.removeEventListener('keydown', handleKeydown, true)

  // Exit fullscreen if in it
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(() => {})
  }
}
