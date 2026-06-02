import uuid
from sqlalchemy import String, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import UUIDBase


class Subscription(UUIDBase):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="inactive")  # active | past_due | canceled | trialing
    plan_type: Mapped[str] = mapped_column(String(20))  # monthly | annual
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_sub_id: Mapped[str | None] = mapped_column(String(255))
    current_period_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    price_id: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[float | None] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<Subscription user={self.user_id} status={self.status}>"
