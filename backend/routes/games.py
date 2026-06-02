import uuid
import random
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.schemas.games import (
    QuestionResponse,
    GameSessionCreate,
    GameSessionResponse,
    SkillMasteryResponse,
    SkillMasteryList,
    GameRecommendation,
)
from backend.utils.security import get_current_user
from backend.models.user import User
from backend.models.child_profile import ChildProfile
from backend.models.game_session import GameSession
from backend.models.bkt_state import BKTState
from backend.models.subject import Subject
from backend.models.game_level import GameLevel
from backend.models.question import Question
from backend.services.bkt_engine import BKTEngine, BKTState as BKTModel

router = APIRouter(prefix="/api/games", tags=["games"])

bkt_engine = BKTEngine()

# Mock question bank for development
MOCK_QUESTIONS = {
    "MATH": [
        {
            "skill_id": "math_add_01",
            "difficulty": 1,
            "content": {"text": "3 + 5 = ?", "type": "choice", "options": ["6", "7", "8", "9"], "answer": "8"},
        },
        {
            "skill_id": "math_add_01",
            "difficulty": 2,
            "content": {"text": "12 + 7 = ?", "type": "choice", "options": ["17", "18", "19", "20"], "answer": "19"},
        },
        {
            "skill_id": "math_sub_01",
            "difficulty": 1,
            "content": {"text": "9 - 4 = ?", "type": "choice", "options": ["3", "4", "5", "6"], "answer": "5"},
        },
        {
            "skill_id": "math_mul_01",
            "difficulty": 2,
            "content": {"text": "3 × 4 = ?", "type": "choice", "options": ["7", "10", "12", "15"], "answer": "12"},
        },
        {
            "skill_id": "math_div_01",
            "difficulty": 2,
            "content": {"text": "12 ÷ 3 = ?", "type": "choice", "options": ["3", "4", "5", "6"], "answer": "4"},
        },
    ],
    "CHIN": [
        {
            "skill_id": "chinese_pinyin_01",
            "difficulty": 1,
            "content": {"text": "「天」的拼音係咩？", "type": "choice", "options": ["tiān", "tān", "diān", "tiàn"], "answer": "tiān"},
        },
        {
            "skill_id": "chinese_char_01",
            "difficulty": 2,
            "content": {"text": "「貓」有幾多畫？", "type": "choice", "options": ["13", "14", "15", "16"], "answer": "14"},
        },
    ],
    "LOGIC": [
        {
            "skill_id": "logic_pattern_01",
            "difficulty": 2,
            "content": {"text": "2, 4, 6, 8, ? 下一數係咩？", "type": "choice", "options": ["9", "10", "11", "12"], "answer": "10"},
        },
    ],
    "SCI": [
        {
            "skill_id": "sci_nature_01",
            "difficulty": 1,
            "content": {"text": "植物需要咩嚟光合作用？", "type": "choice", "options": ["陽光", "月亮", "風", "雪"], "answer": "陽光"},
        },
    ],
    "MUSIC": [
        {
            "skill_id": "music_note_01",
            "difficulty": 1,
            "content": {"text": "C大調有幾多個音？", "type": "choice", "options": ["5", "6", "7", "8"], "answer": "7"},
        },
    ],
}


@router.get("/subjects")
async def list_subjects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.is_active == True))
    return result.scalars().all()


@router.get("/questions/recommend", response_model=QuestionResponse)
async def recommend_question(
    child_id: uuid.UUID,
    subject: str = Query(default="MATH"),
    count: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recommended questions based on BKT mastery."""
    # Check child belongs to user
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.user_id == current_user.id,
        )
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")

    # Get mock questions for this subject
    questions = MOCK_QUESTIONS.get(subject, MOCK_QUESTIONS["MATH"])

    # Get BKT state for this child
    bkt_result = await db.execute(
        select(BKTState).where(
            BKTState.child_id == child_id,
            BKTState.skill_id.in_([q["skill_id"] for q in questions]),
        )
    )
    bkt_states = {s.skill_id: s for s in bkt_result.scalars().all()}

    # Score questions by BKT (lower mastery = higher priority)
    scored = []
    for q in questions:
        bkt = bkt_states.get(q["skill_id"])
        if bkt:
            priority = 1.0 - bkt.p_l  # Lower mastery = higher priority
        else:
            priority = 0.5  # New skill = medium priority
        scored.append((q, priority))

    # Sort by priority descending, pick top N
    scored.sort(key=lambda x: x[1], reverse=True)
    selected = [q for q, _ in scored[:count]]

    return QuestionResponse(
        questions=selected,
        child_id=child_id,
        subject=subject,
    )


@router.post("/session", response_model=GameSessionResponse)
async def submit_answer(
    data: GameSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an answer and get feedback."""
    # Verify child
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == data.child_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")

    # Get question
    q_result = await db.execute(
        select(Question).where(Question.id == data.question_id)
    )
    question = q_result.scalar_one_or_none()

    if not question:
        # Use mock question
        is_correct = random.random() < 0.7  # Mock: 70% correct
        xp = 10 if is_correct else 0
        stars = 1 if is_correct else 0
    else:
        is_correct = data.answer.lower().strip() == question.answer.lower().strip()
        xp = 10 * question.difficulty if is_correct else 0
        stars = 1 if is_correct else 0

    # Update BKT
    bkt = bkt_engine.update(str(data.child_id), question.skill_id if question else data.skill_id, is_correct)

    # Create session record
    session = GameSession(
        child_id=data.child_id,
        game_type=data.game_type,
        question_id=data.question_id,
        skill_id=data.skill_id,
        is_correct=is_correct,
        time_taken=data.time_taken,
        xp_earned=xp,
        stars_earned=stars,
        metadata_={"predicted_correct": bkt.predict_correct()},
    )
    db.add(session)

    # Update child totals
    child.xp_total += xp
    child.stars_total += stars
    child.last_active_date = __import__("datetime").date.today().isoformat()

    # Update BKT in DB
    bkt_record = await db.execute(
        select(BKTState).where(
            BKTState.child_id == data.child_id,
            BKTState.skill_id == (question.skill_id if question else data.skill_id),
        )
    )
    bkt_db = bkt_record.scalar_one_or_none()
    if bkt_db:
        bkt_db.p_l = bkt.p_l
        bkt_db.total_attempts = bkt.attempts
        bkt_db.correct_attempts = bkt.correct
        bkt_db.last_practiced = __import__("datetime").date.today().isoformat()
    else:
        bkt_db = BKTState(
            child_id=data.child_id,
            skill_id=question.skill_id if question else data.skill_id,
            p_l=bkt.p_l,
            p_t=bkt.p_t,
            p_g=bkt.p_g,
            p_s=bkt.p_s,
            total_attempts=bkt.attempts,
            correct_attempts=bkt.correct,
            last_practiced=__import__("datetime").date.today().isoformat(),
        )
        db.add(bkt_db)

    await db.flush()

    return GameSessionResponse(
        session_id=str(session.id),
        is_correct=is_correct,
        xp_earned=xp,
        stars_earned=stars,
        feedback="太叻啦！答啱晒！🎉" if is_correct else "差少少，再試一次！💪",
        mastery_score=round(bkt.p_l, 3),
    )


@router.get("/mastery/{child_id}", response_model=SkillMasteryList)
async def get_mastery(
    child_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == child_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")

    bkt_result = await db.execute(
        select(BKTState).where(BKTState.child_id == child_id)
    )
    states = bkt_result.scalars().all()

    skills = [
        SkillMasteryResponse(
            skill_id=s.skill_id,
            mastery_score=s.p_l,
            attempts=s.total_attempts,
            correct_attempts=s.correct_attempts,
        )
        for s in states
    ]

    return SkillMasteryList(child_id=child_id, skills=skills)


@router.get("/recommend/{child_id}", response_model=GameRecommendation)
async def get_recommendation(
    child_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized game recommendations."""
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == child_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")

    bkt_result = await db.execute(
        select(BKTState).where(BKTState.child_id == child_id)
    )
    states = bkt_result.scalars().all()

    # Find weakest skill
    weakest = None
    for s in states:
        if weakest is None or s.p_l < weakest.p_l:
            weakest = s

    # Find overlearned skill (mastery > 0.95)
    overlearned = [s for s in states if s.p_l > 0.95]

    return GameRecommendation(
        child_id=child_id,
        next_skill=weakest.skill_id if weakest else None,
        review_skills=[s.skill_id for s in overlearned],
        suggested_subject=weakest.skill_id.split("_")[0].upper() if weakest else "MATH",
        suggested_difficulty=max(1, min(5, int(weakest.p_l * 5) + 1)) if weakest else 1,
    )
