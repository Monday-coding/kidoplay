from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="KidoPlay API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發階段
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChildProfile(BaseModel):
    id: int
    name: str
    age: int
    grade: str
    learning_level: Optional[float] = 0.5

class GameSession(BaseModel):
    child_id: int
    game_type: str
    score: int
    xp_earned: int
    skills_practiced: List[str]

# Routes
@app.get("/")
def root():
    return {"message": "KidoPlay API is running"}

@app.get("/api/v1/profile/{child_id}")
def get_profile(child_id: int):
    # TODO: 從 DB 獲取數據
    return {"id": child_id, "name": "Example Child", "grade": "P1"}

@app.post("/api/v1/game/session")
def start_game_session(session: GameSession):
    # TODO: 記錄遊戲開始，觸發 AI 排課
    return {"status": "started", "session_id": 123}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
