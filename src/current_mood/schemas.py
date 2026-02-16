from pydantic import BaseModel

class AgentCurrentMood(BaseModel):
    joy: float
    saddness: float
    anger: float
    fear: float
    color: str
