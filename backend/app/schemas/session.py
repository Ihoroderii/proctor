from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    exam_id: int
    candidate_identifier: str | None = None


class SessionCreateResponse(BaseModel):
    session_id: int
    room_name: str


class JoinRequest(BaseModel):
    exam_code: str
    candidate_identifier: str


class JoinResponse(BaseModel):
    session_id: int
    room_name: str


class AgentEventRequest(BaseModel):
    session_id: int
    event_type: str
    payload: dict | None = None
