import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.schemas.admin import (
    AdminUserList,
    AdminUserDetail,
    AdminChildProfileDetail,
    AdminGameSessionList,
    AdminSubjectList,
    AdminQuestionCreate,
    AdminQuestionResponse,
)
from backend.utils.security import get_current_user, require_admin
from backend.models.user import User
from backend.models.child_profile import ChildProfile
from backend.models.game_session import GameSession
from backend.models.subject import Subject
from backend.models.question import Question
from backend.models.bkt_state import BKTState

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=AdminUserList)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar()

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    return AdminUserList(
        total=total,
        page=page,
        page_size=page_size,
        users=[
            AdminUserDetail(
                id=u.id,
                email=u.email,
                name=u.name,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at.isoformat() if u.created_at else None,
                children_count=len(u.children) if hasattr(u, 'children') else 0,
            )
            for u in users
        ],
    )


@router.get("/children", response_model=AdminChildProfileDetail)
async def get_child_detail(
    child_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == child_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")

    # Get sessions
    session_result = await db.execute(
        select(GameSession).where(GameSession.child_id == child_id).order_by(GameSession.created_at.desc()).limit(50)
    )
    sessions = session_result.scalars().all()

    # Get BKT states
    bkt_result = await db.execute(
        select(BKTState).where(BKTState.child_id == child_id)
    )
    bkt_states = bkt_result.scalars().all()

    return AdminChildProfileDetail(
        id=child.id,
        user_id=child.user_id,
        name=child.name,
        age=child.age,
        grade=child.grade,
        language=child.language,
        xp_total=child.xp_total,
        stars_total=child.stars_total,
        streak_days=child.streak_days,
        sessions=[
            {
                "id": str(s.id),
                "game_type": s.game_type,
                "is_correct": s.is_correct,
                "xp_earned": s.xp_earned,
                "time_taken": s.time_taken,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
        bkt_states=[
            {
                "skill_id": s.skill_id,
                "p_l": s.p_l,
                "attempts": s.total_attempts,
                "correct": s.correct_attempts,
            }
            for s in bkt_states
        ],
    )


@router.get("/subjects", response_model=list[AdminSubjectList])
async def list_subjects(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subject).order_by(Subject.name))
    return result.scalars().all()


@router.post("/questions", response_model=AdminQuestionResponse)
async def create_question(
    data: AdminQuestionCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    question = Question(
        subject_id=data.subject_id,
        skill_id=data.skill_id,
        difficulty=data.difficulty,
        content=data.content,
        answer=data.answer,
        explanation=data.explanation,
    )
    db.add(question)
    await db.flush()
    await db.refresh(question)

    return AdminQuestionResponse(
        id=question.id,
        subject_id=question.subject_id,
        skill_id=question.skill_id,
        difficulty=question.difficulty,
        content=question.content,
        answer=question.answer,
        explanation=question.explanation,
    )


@router.get("/questions", response_model=list[AdminQuestionResponse])
async def list_questions(
    subject: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Question)
    if subject:
        query = query.where(Question.subject_id == subject)
    if skill:
        query = query.where(Question.skill_id == skill)
    query = query.order_by(Question.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    await db.delete(question)
    return {"message": "Question deleted"}
