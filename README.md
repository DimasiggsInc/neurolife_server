# neurolife_server





# API
Базовый путь: `/api/v1`

# Agent
## `GET /agents`
### Краткая инфа о всех агентах
**Параметры запроса**  
| Параметр | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `active_only` | boolean | Только активные агенты | `true` |
| `limit` | integer | Макс. количество | `20` |
### Response:
```json
{
  "agents": [
    {
      "id": "61f0c404-5cb3-11e7-907b-a6006ad3dba0",
      "name": "Лира",
      "avatar": "Base64",
      "mood": {
        "joy": 0.5,
        "sadness": 0.5,
        "anger": 0.5,
        "fear": 0.5,
        "color": "#FFD700",
      },
      "is_active": true,
      "last_activity": "2026-02-16T14:28:15Z"
    },
  ],
  "total_count": 1,
  "active_count": 1
}
```
## `GET /agents/{agent_id}`
### Подробная инфа о конкретном агенте по id
**Параметры запроса**  
| Параметр | Тип | Обязательный |
|----------|-----|--------------|
| `agent_id` | uuid | ✅ |

### Response
```json
{
  "agent": {
    "id": "61f0c404-5cb3-11e7-907b-a6006ad3dba0",
    "name": "Лира",
    "avatar_url": "Base64",
    "is_active": true,
    "created_at": "2026-02-16T10:00:00Z",
  },
  "personality": {
    "core_traits": {
      "openness": 0.85,
      "agreeableness": 0.90,
      "neuroticism": 0.25
    },
    "background": "Ботаник-исследователь из далёкой колонии...",
    "speech_style": {
      "formality": 0.7,
      "verbosity": 0.4,
      "emotional_expressiveness": 0.8
    }
  },
  "mood": {
      "joy": 0.5,
      "sadness": 0.5,
      "anger": 0.5,
      "fear": 0.5,
      "color": "#FFD700",
    },
  },
  "relationships": [
    {
      "agent_id": "61f0c404-5cb3-11e7-907b-a6006ad3dba0",
      "name": "Кай",
      "affinity": 0.78,
      "last_interaction": "2026-02-16T14:25:10Z",
      "history_summary": "Помогал собирать семена вчера"
    },
  ]
}
```


#### `POST /agents` Создание нового агента
