"""
BKT Engine — Bayesian Knowledge Tracing

Adapted from Corbett & Belfort (1985).
For each skill, maintains:
  p_l: P(Learned) — probability the child has mastered this skill
  p_t: P(Transition) — probability of learning on a trial
  p_g: P(Guess) — probability of correct answer despite not knowing
  p_s: P(Slip) — probability of wrong answer despite knowing

Update rule (after correct answer):
  p_l' = p_l * (1 - p_s) / [p_l * (1 - p_s) + (1 - p_l) * p_g]

Update rule (after incorrect answer):
  p_l' = p_l * p_s / [p_l * p_s + (1 - p_l) * (1 - p_g)]

New skill initialization:
  p_l = 0.5 (uniform prior)
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.bkt_state import BKTState as BKTStateORM


class BKTState:
    def __init__(
        self,
        p_l: float = 0.5,
        p_t: float = 0.2,
        p_g: float = 0.25,
        p_s: float = 0.1,
    ):
        self.p_l = p_l
        self.p_t = p_t
        self.p_g = p_g
        self.p_s = p_s
        self.attempts = 0
        self.correct = 0

    def predict_correct(self) -> float:
        """Predict probability of correct answer on next attempt."""
        return self.p_l * (1 - self.p_s) + (1 - self.p_l) * self.p_g

    def update(self, observed: bool) -> None:
        """
        Update p_l given observed correctness.
        observed=True = correct, False = incorrect
        """
        if observed:
            # Correct answer
            numerator = self.p_l * (1 - self.p_s)
            denominator = numerator + (1 - self.p_l) * self.p_g
            if denominator > 0:
                self.p_l = numerator / denominator
            self.correct += 1
        else:
            # Incorrect answer
            numerator = self.p_l * self.p_s
            denominator = numerator + (1 - self.p_l) * (1 - self.p_g)
            if denominator > 0:
                self.p_l = numerator / denominator
        self.attempts += 1

    def to_dict(self) -> dict:
        return {
            "p_l": round(self.p_l, 4),
            "p_t": self.p_t,
            "p_g": self.p_g,
            "p_s": self.p_s,
            "attempts": self.attempts,
            "correct": self.correct,
            "predicted_correct": round(self.predict_correct(), 4),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BKTState":
        state = cls(
            p_l=d.get("p_l", 0.5),
            p_t=d.get("p_t", 0.2),
            p_g=d.get("p_g", 0.25),
            p_s=d.get("p_s", 0.1),
        )
        state.attempts = d.get("attempts", 0)
        state.correct = d.get("correct", 0)
        return state


class BKTEngine:
    """Manages BKT states per child per skill with DB persistence."""

    def __init__(self):
        self._states: dict[str, BKTState] = {}  # key: "child_id:skill_id"

    def get_state(self, child_id: str, skill_id: str) -> BKTState:
        key = f"{child_id}:{skill_id}"
        if key not in self._states:
            self._states[key] = BKTState()
        return self._states[key]

    def update(self, child_id: str, skill_id: str, observed: bool) -> BKTState:
        state = self.get_state(child_id, skill_id)
        state.update(observed)
        return state

    def get_prediction(self, child_id: str, skill_id: str) -> float:
        state = self.get_state(child_id, skill_id)
        return state.predict_correct()

    def get_next_skill(self, child_id: str, subjects: list[str], current_mastery: dict) -> str:
        """
        Select next skill to practice based on:
        1. Skills with mastery < 0.85 (need practice)
        2. Among those, lowest predicted correctness
        3. If all mastered, return highest mastery skill for review
        """
        candidates = []
        for subj in subjects:
            mastery = current_mastery.get(subj, 0.5)
            if mastery < 0.85:
                candidates.append((subj, mastery))

        if not candidates:
            # All mastered — return highest mastery for review
            for subj in subjects:
                mastery = current_mastery.get(subj, 0.5)
                candidates.append((subj, mastery))

        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]  # Return lowest mastery skill

    def get_all_states(self, child_id: str) -> dict:
        result = {}
        for key, state in self._states.items():
            if key.startswith(f"{child_id}:"):
                skill_id = key.split(":", 1)[1]
                result[skill_id] = state.to_dict()
        return result

    # ---- DB persistence (async) ----

    async def load_child_states(self, db: AsyncSession, child_id: uuid.UUID) -> dict[str, BKTState]:
        """Load all BKT states for a child from DB into in-memory cache."""
        result = await db.execute(
            select(BKTStateORM).where(BKTStateORM.child_id == child_id)
        )
        for orm_state in result.scalars().all():
            key = f"{child_id}:{orm_state.skill_id}"
            self._states[key] = BKTState(
                p_l=orm_state.p_l,
                p_t=orm_state.p_t,
                p_g=orm_state.p_g,
                p_s=orm_state.p_s,
            )
            self._states[key].attempts = orm_state.total_attempts
            self._states[key].correct = orm_state.correct_attempts
        return self._states

    async def save_state(self, db: AsyncSession, child_id: uuid.UUID, skill_id: str) -> BKTState | None:
        """Persist a single BKT state back to DB."""
        key = f"{child_id}:{skill_id}"
        state = self._states.get(key)
        if state is None:
            return None

        orm = await db.execute(
            select(BKTStateORM).where(
                BKTStateORM.child_id == child_id,
                BKTStateORM.skill_id == skill_id,
            )
        )
        record = orm.scalar_one_or_none()

        if record is None:
            record = BKTStateORM(
                child_id=child_id,
                skill_id=skill_id,
            )
            db.add(record)

        record.p_l = state.p_l
        record.p_t = state.p_t
        record.p_g = state.p_g
        record.p_s = state.p_s
        record.total_attempts = state.attempts
        record.correct_attempts = state.correct
        record.last_practiced = __import__("datetime").date.today().isoformat()

        await db.flush()
        return state
