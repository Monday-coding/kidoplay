import uuid
from sqlalchemy import String, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class GameLevel(UUIDBase):
    __tablename__ = "game_levels"

    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("child_profiles.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "math_add_01"
    skill_name: Mapped[str] = mapped_column(String(100), nullable=True)
    skill_level: Mapped[dict | None] = mapped_column(JSON, default=dict)  # tier, sub_skills
    mastery: Mapped[dict | None] = mapped_column(JSON, default=dict)  # skill_id -> mastery_score
    overall_mastery: Mapped[float] = mapped_column(default=0.0)
    next_review_date: Mapped[str | None] = mapped_column(String(10), nullable=True)

    child: Mapped["ChildProfile"] = relationship(back_populates="game_levels")
    subject: Mapped["Subject"] = relationship(back_populates="game_levels")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<GameLevel child={self.child_id} skill={self.skill_id}>"
