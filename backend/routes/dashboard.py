import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import get_db
from backend.schemas.dashboard import (
    DashboardOverview,
    WeeklyActivity,
    SubjectBreakdown,
    Milestone,
    Recommendation,
)
from backend.utils.security import get_current_user
from backend.models.user import User
from backend.models.child_profile import ChildProfile
from backend.models.game_session import GameSession
from backend.models.bkt_state import BKTState
from backend.models.achievement import Achievement
from backend.models.subject import Subject
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{child_id}")
async def get_dashboard(
    child_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get child profile
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == child_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Weekly activity (last 7 days)
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    session_result = await db.execute(
        select(GameSession).where(
            GameSession.child_id == child_id,
            GameSession.created_at >= week_ago,
        ).order_by(GameSession.created_at)
    )
    sessions = session_result.scalars().all()

    daily_xp = {}
    daily_sessions = {}
    for s in sessions:
        day = s.created_at.strftime("%Y-%m-%d") if s.created_at else "unknown"
        daily_xp[day] = daily_xp.get(day, 0) + (s.xp_earned or 0)
        daily_sessions[day] = daily_sessions.get(day, 0) + 1

    weekly_activity = [
        WeeklyActivity(
            date=day,
            xp_earned=daily_xp.get(day, 0),
            sessions=daily_sessions.get(day, 0),
        )
        for day in sorted(daily_xp.keys())
    ]

    # Subject breakdown
    subject_result = await db.execute(
        select(Subject).where(Subject.is_active == True)
    )
    subjects = subject_result.scalars().all()

    subject_breakdown = []
    for subj in subjects:
        subj_sessions = [s for s in sessions if s.skill_id and s.skill_id.startswith(subj.code.lower())]
        correct = sum(1 for s in subj_sessions if s.is_correct)
        total = len(subj_sessions)
        subject_breakdown.append(
            SubjectBreakdown(
                subject=subj.code,
                name=subj.name,
                sessions=total,
                accuracy=round(correct / total * 100, 1) if total > 0 else 0,
                xp_earned=sum(s.xp_earned or 0 for s in subj_sessions),
            )
        )

    # Milestones (recent achievements)
    ach_result = await db.execute(
        select(Achievement).where(
            Achievement.child_id == child_id
        ).order_by(Achievement.earned_at.desc()).limit(5)
    )
    milestones = ach_result.scalars().all()

    # Recommendations
    bkt_result = await db.execute(
        select(BKTState).where(BKTState.child_id == child_id)
    )
    bkt_states = bkt_result.scalars().all()

    # Find skills needing practice
    needs_practice = [s for s in bkt_states if s.p_l < 0.7]
    review_skills = [s for s in bkt_states if 0.7 <= s.p_l < 0.9]

    recommendations = []
    for s in needs_practice[:3]:
        recommendations.append(
            Recommendation(
                type="practice",
                skill_id=s.skill_id,
                description=f"需要練習：{s.skill_id} (掌握度 {s.p_l:.0%})",
                priority="high" if s.p_l < 0.5 else "medium",
            )
        )
    for s in review_skills[:2]:
        recommendations.append(
            Recommendation(
                type="review",
                skill_id=s.skill_id,
                description=f"複習：{s.skill_id} (掌握度 {s.p_l:.0%})",
                priority="low",
            )
        )

    return DashboardOverview(
        child_id=child.id,
        name=child.name,
        xp_total=child.xp_total,
        stars_total=child.stars_total,
        streak_days=child.streak_days,
        weekly_activity=weekly_activity,
        subject_breakdown=subject_breakdown,
        milestones=[
            {"name": m.name, "icon": m.icon, "earned_at": m.earned_at}
            for m in milestones
        ],
        recommendations=recommendations,
    )
