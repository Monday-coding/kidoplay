from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID

class QuestionResponse(BaseModel):
    questions: List[Dict[str, Any]]
    child_id: UUID
    subject: str

    class Config:
        from_attributes = True

class GameSessionCreate(BaseModel):
    child_id: UUID
    game_type: str
    question_id: Optional[UUID] = None
    skill_id: str
    answer: str
    time_taken: Optional[float] = None

class GameSessionResponse(BaseModel):
    session_id: str
    is_correct: bool
    xp_earned: int
    stars_earned: int
    feedback: str
    mastery_score: float

    class Config:
        from_attributes = True

class SkillMasteryResponse(BaseModel):
    skill_id: str
    mastery_score: float
    attempts: int
    correct_attempts: int

class SkillMasteryList(BaseModel):
    child_id: UUID
    skills: List[SkillMasteryResponse]

    class Config:
        from_attributes = True

class GameRecommendation(BaseModel):
    child_id: UUID
    next_skill: Optional[str] = None
    review_skills: List[str] = []
    suggested_subject: str
    suggested_difficulty: int

    class Config:
        from_attributes = True
