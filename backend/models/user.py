import uuid
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class User(UUIDBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="parent")  # parent | admin
    is_active: Mapped[bool] = mapped_column(default=True)

    children: Mapped[list["ChildProfile"]] = relationship(back_populates="parent", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
