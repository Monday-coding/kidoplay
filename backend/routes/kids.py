import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import get_db
from backend.schemas.kids import (
    ChildProfileCreate,
    ChildProfileOut,
    ChildProfileDetail,
    UpdateChildProfileRequest,
    UpdatePinRequest,
)
from backend.utils.security import get_current_user
from backend.models.user import User
from backend.models.child_profile import ChildProfile
from backend.models.bkt_state import BKTState
from backend.models.achievement import Achievement
from backend.models.subscription import Subscription
from backend.services.bkt_engine import BKTEngine
from backend.services.auth_service import get_user_subscription

router = APIRouter(prefix="/api/kids", tags=["kids"])

bkt_engine = BKTEngine()


def _build_detail(profile: ChildProfile, db: AsyncSession) -> ChildProfileDetail:
    """Build full detail with related data."""
    detail = ChildProfileOut.model_validate(profile)

    # BKT states
    bkt_result = db.execute(
        select(BKTState).where(BKTState.child_id == profile.id)
    )
    bkt_states = bkt_result.scalars().all()
    detail.bkt_states = [
        {
            "skill_id": s.skill_id,
            "p_l": s.p_l,
            "attempts": s.total_attempts,
            "correct_attempts": s.correct_attempts,
        }
        for s in bkt_states
    ]

    # Achievements
    ach_result = db.execute(
        select(Achievement).where(Achievement.child_id == profile.id).order_by(Achievement.earned_at.desc())
    )
    achievements = ach_result.scalars().all()
    detail.achievements = [
        {"name": a.name, "icon": a.icon, "earned_at": a.earned_at}
        for a in achievements
    ]

    # Subscription
    sub = get_user_subscription(db, profile.user_id)
    detail.subscription = {"status": sub.status, "plan_type": sub.plan_type} if sub else None

    return detail


@router.get("", response_model=list[ChildProfileOut])
async def list_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("", response_model=ChildProfileDetail)
async def create_profile(
    data: ChildProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    child = ChildProfile(
        user_id=current_user.id,
        name=data.name,
        age=data.age,
        grade=data.grade,
        language=data.language,
    )
    if data.pin:
        from backend.utils.auth import hash_password
        child.pin_hash = hash_password(data.pin)

    db.add(child)
    await db.flush()
    await db.refresh(child)
    return _build_detail(child, db)


@router.get("/{child_id}", response_model=ChildProfileDetail)
async def get_profile(
    child_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.user_id == current_user.id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _build_detail(profile, db)


@router.patch("/{child_id}", response_model=ChildProfileDetail)
async def update_profile(
    child_id: uuid.UUID,
    data: UpdateChildProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.user_id == current_user.id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)
    return _build_detail(profile, db)


@router.post("/{child_id}/pin", response_model=ChildProfileOut)
async def update_pin(
    child_id: uuid.UUID,
    data: UpdatePinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.user_id == current_user.id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    from backend.utils.auth import hash_password
    profile.pin_hash = hash_password(data.pin)
    await db.flush()
    await db.refresh(profile)
    return profile


@router.delete("/{child_id}")
async def delete_profile(
    child_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.user_id == current_user.id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await db.delete(profile)
    return {"message": "Profile deleted"}
