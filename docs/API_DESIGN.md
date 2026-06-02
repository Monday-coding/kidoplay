# KidoPlay API 規格書 (MVP 階段)

## 1. 規範概覽
- **Base URL**: `/api/v1`
- **Auth**: JWT (Bearer Token) + Refresh Token
- **Data Format**: JSON
- **Language**: zh-HK (Default) / en (via `Accept-Language` header)

## 2. 認證模組 (Auth)
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | 家長登入 (Email/Password) | No |
| `POST` | `/auth/refresh` | 刷新 Access Token | No |
| `POST` | `/auth/child-verify-pin` | 兒童進入驗證 (PIN) | Parent Token |
| `POST` | `/auth/logout` | 登出 | Token |

## 3. 兒童檔案模組 (Kids)
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/kids/{id}` | 獲取兒童檔案 (進度/等級) | Parent Token |
| `GET` | `/kids/{id}/daily-plan` | **AI 排課**：獲取今日學習計畫 | Parent/Child Token |
| `POST` | `/kids/{id}/games/start` | 開始遊戲 (返回題目包) | Parent/Child Token |
| `POST` | `/kids/{id}/games/submit` | 提交答案 (更新 BKT 狀態) | Parent/Child Token |
| `GET` | `/kids/{id}/achievements` | 獲取成就列表 | Parent Token |

## 4. 報告模組 (Reports)
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/kids/{id}/reports/weekly` | 獲取週報 (LLM 生成摘要) | Parent Token |
| `GET` | `/kids/{id}/reports/monthly` | 獲取月報 (技能掌握度圖表) | Parent Token |

## 5. 訂閱模組 (Subscription)
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/subscription/status` | 獲取訂閱狀態 | Parent Token |
| `POST` | `/subscription/checkout` | 生成 Stripe Checkout Session | Parent Token |

---

## 詳細 API 說明

### 5.1 獲取今日學習計畫 (AI 排課)
**Endpoint**: `GET /kids/{id}/daily-plan`
**Logic**: 
1. 查詢 `bkt_state` 表獲取最新掌握度。
2. 篩選 `P(Learned)` 在 0.4-0.8 之間嘅技能 (Zone of Proximal Development)。
3. 混合少量已掌握技能 (Spaced Repetition) 同新技能。
4. 返回 5-8 道題目建議。

**Response**:
```json
{
  "plan_id": "plan_123",
  "items": [
    {
      "skill_id": "math_add_01",
      "game_type": "math_race",
      "difficulty": 2,
      "priority": "high"
    }
  ],
  "estimated_time_min": 15
}
```

### 5.2 提交答案 (更新 BKT)
**Endpoint**: `POST /kids/{id}/games/submit`
**Request**:
```json
{
  "session_id": "sess_456",
  "skill_id": "math_add_01",
  "is_correct": true,
  "time_taken_sec": 12
}
```
**Logic**:
1. 更新 `bkt_state` 中該技能嘅四參數 (`p_l`, `p_t`, `p_g`, `p_s`)。
2. 記錄 `game_sessions` 日志。
3. 計算 XP 同 Stars 獎勵。

**Response**:
```json
{
  "xp_earned": 10,
  "stars_earned": 1,
  "new_mastery": 0.85,
  "next_skill_id": "math_sub_01"
}
```

---

## 6. 錯誤碼規範
- `400`: 參數錯誤 (如 PIN 碼錯誤)
- `401`: 認證失敗 (Token 過期)
- `403`: 權限不足 (如兒童模式嘗試修改設定)
- `404`: 資源不存在
- `429`: 請求過頻 (防呆機制)
- `500`: 伺服器內部錯誤
