#!/usr/bin/env python3
"""
Automated proctor agent: joins a LiveKit room, subscribes to the candidate's camera,
runs face detection, and POSTs face_detected / face_missing to the backend.
Run one process per session. Example:
  python proctor_agent.py --session-id 1 --backend-url http://localhost:8000 --agent-secret your-secret
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Optional: add parent for local backend imports (not required at runtime)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("proctor_agent")


def parse_args():
    p = argparse.ArgumentParser(description="Proctor agent: join room, detect face, post events")
    p.add_argument("--session-id", type=int, required=True, help="Exam session ID")
    p.add_argument("--backend-url", type=str, default="http://localhost:8000", help="Backend base URL")
    p.add_argument("--agent-secret", type=str, required=True, help="X-Agent-Secret for /api/internal/agent-event")
    p.add_argument("--interval", type=float, default=1.0, help="Seconds between face checks")
    return p.parse_args()


async def get_agent_token(backend_url: str, session_id: int) -> tuple[str, str]:
    """POST /api/token/agent -> (token, livekit_url)."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{backend_url.rstrip('/')}/api/token/agent",
            json={"session_id": session_id},
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"token/agent failed {resp.status}: {text}")
            data = await resp.json()
            return data["token"], data["livekit_url"]


async def post_agent_event(
    backend_url: str,
    agent_secret: str,
    session_id: int,
    event_type: str,
    payload: dict | None = None,
) -> None:
    """POST /api/internal/agent-event with X-Agent-Secret."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{backend_url.rstrip('/')}/api/internal/agent-event",
            headers={"X-Agent-Secret": agent_secret, "Content-Type": "application/json"},
            json={
                "session_id": session_id,
                "event_type": event_type,
                "payload": payload or {},
            },
        ) as resp:
            if resp.status not in (200, 204):
                text = await resp.text()
                logger.warning("agent-event %s: %s %s", event_type, resp.status, text)


def detect_face_in_frame(frame) -> bool:
    """Run OpenCV Haar cascade face detection on a LiveKit VideoFrame. Returns True if at least one face."""
    import numpy as np
    import cv2

    w, h = frame.width, frame.height
    data = frame.data
    if not data or w <= 0 or h <= 0:
        return False
    try:
        arr = np.frombuffer(data, dtype=np.uint8)
        # RGBA or similar 4-channel
        if len(arr) >= w * h * 4:
            arr = arr.reshape((h, w, 4))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        elif len(arr) >= w * h * 3:
            arr = arr.reshape((h, w, 3))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        else:
            return False
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return len(faces) > 0
    except Exception as e:
        logger.debug("detect_face_in_frame error: %s", e)
        return False


async def run_face_loop(
    video_stream,
    backend_url: str,
    agent_secret: str,
    session_id: int,
    interval: float,
) -> None:
    """Sample one frame every `interval` seconds, run face detection, POST events on change."""
    last_seen_face = True
    try:
        async for event in video_stream:
            frame = event.frame
            has_face = detect_face_in_frame(frame)
            if has_face and not last_seen_face:
                await post_agent_event(backend_url, agent_secret, session_id, "face_detected", {})
                last_seen_face = True
            elif not has_face and last_seen_face:
                await post_agent_event(backend_url, agent_secret, session_id, "face_missing", {})
                last_seen_face = False
            # Sample at most every `interval` seconds
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.exception("face loop error: %s", e)


async def main_async(args):
    from livekit import rtc

    token, livekit_url = await get_agent_token(args.backend_url, args.session_id)
    logger.info("Got token for session %s, connecting to room", args.session_id)

    room = rtc.Room()
    video_stream = None
    face_task = None

    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        nonlocal video_stream, face_task
        if track.kind != rtc.TrackKind.KIND_VIDEO:
            return
        # Prefer camera (we could filter by TrackSource.CAMERA)
        if video_stream is not None:
            return
        logger.info("Subscribed to video track from %s", participant.identity)
        try:
            video_stream = rtc.VideoStream(track)
            face_task = asyncio.create_task(
                run_face_loop(
                    video_stream,
                    args.backend_url,
                    args.agent_secret,
                    args.session_id,
                    args.interval,
                )
            )
        except Exception as e:
            logger.exception("Failed to start face loop: %s", e)

    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        nonlocal face_task
        if face_task and not face_task.done():
            face_task.cancel()

    room.on("track_subscribed", on_track_subscribed)
    room.on("track_unsubscribed", on_track_unsubscribed)

    await room.connect(livekit_url, token)
    logger.info("Connected to room %s", room.name)

    try:
        while True:
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass
    finally:
        if face_task and not face_task.done():
            face_task.cancel()
            try:
                await face_task
            except asyncio.CancelledError:
                pass
        if video_stream:
            await video_stream.aclose()
        await room.disconnect()
        logger.info("Disconnected")


def main():
    args = parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.exception("Fatal: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
