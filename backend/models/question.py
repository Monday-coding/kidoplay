import uuid
from sqlalchemy import String, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class Question(UUIDBase):
    __tablename__ = "questions"

    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    content: Mapped[dict] = mapped_column(JSON, default=dict)  # text, options, image_url, audio_url
    answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[str | None] = mapped_column(String(1000))

    subject: Mapped["Subject"] = relationship(back_populates="questions")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} skill={self.skill_id} diff={self.difficulty}>"
