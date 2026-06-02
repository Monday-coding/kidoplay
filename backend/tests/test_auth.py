import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from datetime import timedelta

from schemas.auth import UserCreate, LoginRequest
from services.auth_service import register_user, login_user
from models.user import User

SECRET_KEY = "test-secret-key-for-jwt-signing-only"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@pytest.fixture
def auth_settings():
    """Override auth settings for testing."""
    from config import settings
    original = settings.secret_key
    settings.secret_key = SECRET_KEY
    settings.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    yield
    settings.secret_key = original


@pytest.mark.asyncio
async def test_register_user(db_session: AsyncSession, auth_settings):
    """Test user registration."""
    data = UserCreate(
        email="test@example.com",
        password="Test1234!",
        name="Test User",
        role="parent",
    )
    user = await register_user(db_session, data)

    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.role == "parent"
    assert user.is_active is True
    assert user.password_hash is not None  # Should be hashed


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session: AsyncSession, auth_settings):
    """Test registration with duplicate email."""
    data1 = UserCreate(
        email="dup@example.com",
        password="Test1234!",
        name="User One",
        role="parent",
    )
    await register_user(db_session, data1)

    data2 = UserCreate(
        email="dup@example.com",
        password="Test1234!",
        name="User Two",
        role="parent",
    )
    with pytest.raises(ValueError, match="Email already registered"):
        await register_user(db_session, data2)


@pytest.mark.asyncio
async def test_register_weak_password(db_session: AsyncSession, auth_settings):
    """Test registration with weak password."""
    data = UserCreate(
        email="weak@example.com",
        password="123",
        name="Weak User",
        role="parent",
    )
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        await register_user(db_session, data)


@pytest.mark.asyncio
async def test_login_user(db_session: AsyncSession, auth_settings):
    """Test user login."""
    # Register first
    reg_data = UserCreate(
        email="login@example.com",
        password="Test1234!",
        name="Login User",
        role="parent",
    )
    await register_user(db_session, reg_data)

    # Login
    login_data = LoginRequest(
        email="login@example.com",
        password="Test1234!",
    )
    result = await login_user(db_session, login_data)

    assert result.access_token is not None
    assert result.refresh_token is not None
    assert result.user is not None
    assert result.user.email == "login@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession, auth_settings):
    """Test login with wrong password."""
    # Register first
    reg_data = UserCreate(
        email="wrong@example.com",
        password="Test1234!",
        name="Wrong User",
        role="parent",
    )
    await register_user(db_session, reg_data)

    # Try wrong password
    login_data = LoginRequest(
        email="wrong@example.com",
        password="WrongPassword!",
    )
    with pytest.raises(ValueError, match="Invalid credentials"):
        await login_user(db_session, login_data)
