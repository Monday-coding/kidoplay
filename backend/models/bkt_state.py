import uuid
from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class BKTState(UUIDBase):
    __tablename__ = "bkt_states"

    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("child_profiles.id"), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(50), nullable=False)
    p_l: Mapped[float] = mapped_column(Float, default=0.5)  # P(Learned)
    p_t: Mapped[float] = mapped_column(Float, default=0.2)  # P(Transition)
    p_g: Mapped[float] = mapped_column(Float, default=0.25)  # P(Guess)
    p_s: Mapped[float] = mapped_column(Float, default=0.1)  # P(Slip)
    total_attempts: Mapped[int] = mapped_column(default=0)
    correct_attempts: Mapped[int] = mapped_column(default=0)
    last_practiced: Mapped[str | None] = mapped_column(String(10), nullable=True)

    child: Mapped["ChildProfile"] = relationship(back_populates="bkt_states")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<BKTState child={self.child_id} skill={self.skill_id} p_l={self.p_l:.3f}>"
