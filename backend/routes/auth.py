from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.schemas.auth import (
    UserCreate,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    UserOut,
)
from backend.services.auth_service import register_user, login_user, get_user_by_id
from backend.utils.security import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await register_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await login_user(db, data)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from backend.utils.auth import decode_token, create_access_token
    from jose import JWTError

    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user = await get_user_by_id(db, __import__("uuid").UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        new_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return RefreshResponse(access_token=new_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
