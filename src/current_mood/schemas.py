from pydantic import BaseModel

class AgentCurrentMood(BaseModel):
    joy: float
    sadness: float
    anger: float
    fear: float
    color: str
