from pydantic import BaseModel, EmailStr


class ProctorLoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProctorLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    proctor_id: int
    email: str
