import uuid
from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class Achievement(UUIDBase):
    __tablename__ = "achievements"

    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("child_profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500))
    icon: Mapped[str] = mapped_column(String(50))  # emoji or icon name
    earned_at: Mapped[str] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD

    child: Mapped["ChildProfile"] = relationship(back_populates="achievements")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<Achievement id={self.id} name={self.name}>"
