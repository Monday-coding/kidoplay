import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.child_profile import ChildProfile
from models.achievement import Achievement
from models.subject import Subject
from services.auth_service import register_user
from schemas.auth import UserCreate
from services.bkt_engine import BKTEngine

SECRET_KEY = "test-secret-key-for-jwt-signing-only"


@pytest.fixture
def auth_settings():
    from config import settings
    original = settings.secret_key
    settings.secret_key = SECRET_KEY
    yield
    settings.secret_key = original


@pytest.mark.asyncio
async def test_child_profile_crud(db_session: AsyncSession, auth_settings):
    """Test child profile creation and retrieval."""
    # Create parent user
    reg_data = UserCreate(
        email="parent@test.com",
        password="Test1234!",
        name="Parent",
        role="parent",
    )
    user = await register_user(db_session, reg_data)

    # Create child profile
    child = ChildProfile(
        user_id=user.id,
        name="小明",
        age=6,
        grade=1,
        language="zh-HK",
    )
    db_session.add(child)
    await db_session.flush()
    await db_session.refresh(child)

    assert child.name == "小明"
    assert child.age == 6
    assert child.xp_total == 0
    assert child.stars_total == 0


@pytest.mark.asyncio
async def test_bkt_state_update(db_session: AsyncSession, auth_settings):
    """Test BKT engine state updates."""
    engine = BKTEngine()

    # Initial state
    state = engine.get("child-1", "math_add_01")
    assert state.p_l == pytest.approx(0.5, abs=0.01)

    # Correct answer
    engine.update("child-1", "math_add_01", True)
    state = engine.get("child-1", "math_add_01")
    assert state.p_l > 0.5  # Should increase

    # Another correct
    engine.update("child-1", "math_add_01", True)
    state = engine.get("child-1", "math_add_01")
    assert state.p_l > 0.7  # Should increase more


@pytest.mark.asyncio
async def test_bkt_wrong_then_correct(db_session: AsyncSession, auth_settings):
    """Test BKT recovery from wrong to correct."""
    engine = BKTEngine()

    # Wrong answers decrease mastery
    engine.update("child-1", "math_add_01", False)
    engine.update("child-1", "math_add_01", False)
    state = engine.get("child-1", "math_add_01")
    assert state.p_l < 0.5

    # Correct answers recover
    engine.update("child-1", "math_add_01", True)
    engine.update("child-1", "math_add_01", True)
    state = engine.get("child-1", "math_add_01")
    assert state.p_l > 0.4  # Should recover


@pytest.mark.asyncio
async def test_subject_creation(db_session: AsyncSession, auth_settings):
    """Test subject data integrity."""
    subject = Subject(
        code="MATH",
        name="Mathematics",
        icon="🔢",
        description="Math skills for kids",
        is_active=True,
    )
    db_session.add(subject)
    await db_session.flush()

    result = await db_session.execute(
        select(Subject).where(Subject.code == "MATH")
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.name == "Mathematics"


@pytest.mark.asyncio
async def test_achievement_tracking(db_session: AsyncSession, auth_settings):
    """Test achievement creation and tracking."""
    # Create parent + child
    reg_data = UserCreate(
        email="ach@test.com",
        password="Test1234!",
        name="Parent",
        role="parent",
    )
    user = await register_user(db_session, reg_data)

    child = ChildProfile(
        user_id=user.id,
        name="小華",
        age=7,
        grade=2,
        language="zh-HK",
    )
    db_session.add(child)
    await db_session.flush()
    await db_session.refresh(child)

    achievement = Achievement(
        child_id=child.id,
        name="First Star",
        icon="⭐",
        description="Earned first star",
        earned_at="2025-01-01",
    )
    db_session.add(achievement)
    await db_session.flush()

    result = await db_session.execute(
        select(Achievement).where(Achievement.child_id == child.id)
    )
    found = result.scalars().all()
    assert len(found) == 1
    assert found[0].name == "First Star"
