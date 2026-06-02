import uuid
from sqlalchemy import String, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class GameSession(UUIDBase):
    __tablename__ = "game_sessions"

    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("child_profiles.id"), nullable=False)
    game_type: Mapped[str] = mapped_column(String(50), nullable=False)  # math_race, word_match, etc.
    question_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("questions.id"))
    skill_id: Mapped[str | None] = mapped_column(String(50))
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    time_taken: Mapped[int | None] = mapped_column(Integer)  # seconds
    xp_earned: Mapped[int] = mapped_column(default=0)
    stars_earned: Mapped[int] = mapped_column(default=0)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)

    child: Mapped["ChildProfile"] = relationship(back_populates="game_sessions")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<GameSession id={self.id} child={self.child_id} type={self.game_type}>"
