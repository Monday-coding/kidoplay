import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    name: str
    role: str = "parent"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ChildProfileCreate(BaseModel):
    name: str
    age: Optional[int] = None
    grade: Optional[str] = None
    language: str = "zh-HK"
    pin: Optional[str] = None


class ChildProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    age: Optional[int]
    grade: Optional[str]
    language: str
    xp_total: int
    stars_total: int
    streak_days: int
    last_active_date: Optional[str]

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None


class UpdatePinRequest(BaseModel):
    pin: str


class UpdateChildProfileRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    grade: Optional[str] = None
    language: Optional[str] = None


class ChildProfileDetail(ChildProfileOut):
    game_levels: list = []
    bkt_states: list = []
    achievements: list = []
    subscription: Optional[dict] = None
