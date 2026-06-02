# KidoPlay

> 香港兒童學習 App — 遊戲化 AI 學習平台

## 項目概覽
面向 K1-K6 兒童嘅粵語原生雙語學習 App，結合遊戲化機制同 AI 個人化排課 (BKT)。

## 技術棧
- **Frontend**: Flutter + Flame Engine
- **Backend**: FastAPI + PostgreSQL
- **AI**: BKT (Bayesian Knowledge Tracing)
- **Infrastructure**: Docker, AWS/GCP

## 目錄結構
- `backend/`: FastAPI 應用程式
- `frontend/`: Flutter 應用程式
- `docs/`: 項目文檔 (Notion 同步)

## 快速開始
```bash
# 啟動後端服務 (PostgreSQL + Redis)
docker-compose up -d

# 啟動後端
cd backend
uvicorn main:app --reload

# 啟動前端
cd frontend
flutter run
```
