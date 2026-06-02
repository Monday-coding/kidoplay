import uuid
from sqlalchemy import String, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class ChildProfile(UUIDBase):
    __tablename__ = "child_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    grade: Mapped[str] = mapped_column(String(10), nullable=True)  # P1-P6
    language: Mapped[str] = mapped_column(String(10), default="zh-HK")  # zh-HK | en
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    xp_total: Mapped[int] = mapped_column(default=0)
    stars_total: Mapped[int] = mapped_column(default=0)
    streak_days: Mapped[int] = mapped_column(default=0)
    last_active_date: Mapped[str] = mapped_column(String(10), nullable=True)

    parent: Mapped["User"] = relationship(back_populates="children")
    game_levels: Mapped[list["GameLevel"]] = relationship(back_populates="child", lazy="selectin")
    game_sessions: Mapped[list["GameSession"]] = relationship(back_populates="child", lazy="selectin")
    bkt_states: Mapped[list["BKTState"]] = relationship(back_populates="child", lazy="selectin")
    achievements: Mapped[list["Achievement"]] = relationship(back_populates="child", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ChildProfile id={self.id} name={self.name}>"
