from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class Subject(UUIDBase):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # MATH, CHIN, LOGIC, SCI, MUSIC
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True)

    game_levels: Mapped[list["GameLevel"]] = relationship(back_populates="subject", lazy="selectin")
    questions: Mapped[list["Question"]] = relationship(back_populates="subject", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Subject id={self.id} code={self.code}>"
