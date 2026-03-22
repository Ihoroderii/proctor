from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    exam_id: int
    candidate_identifier: str | None = None


class SessionCreateResponse(BaseModel):
    session_id: int
    livekit_room_name: str


class TokenRequest(BaseModel):
    session_id: int
    participant_identity: str  # candidate name or "proctor-{id}"


class TokenResponse(BaseModel):
    token: str
    livekit_url: str


class JoinRequest(BaseModel):
    exam_code: str
    candidate_identifier: str


class JoinResponse(BaseModel):
    session_id: int
    livekit_room_name: str
    token: str | None = None
    livekit_url: str | None = None


class AgentTokenRequest(BaseModel):
    session_id: int


class AgentEventRequest(BaseModel):
    session_id: int
    event_type: str
    payload: dict | None = None
