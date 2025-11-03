from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime


class UserInput(BaseModel):
    country: str
    year: int


class A2AMeta(BaseModel):
    message_id: str = Field(..., description="Unique message id")
    sent_at: datetime
    sender: str
    recipient: str
    protocol: Literal["a2a.v1"] = "a2a.v1"


class A2APayload(BaseModel):
    type: str
    content: Dict[str, Any]


class A2AMessage(BaseModel):
    meta: A2AMeta
    payload: A2APayload
    callback_url: Optional[str] = None

    @field_validator("meta")
    @classmethod
    def check_meta_ids(cls, value):
        if not value.message_id or value.message_id.strip() == "":
            raise ValueError("meta.message_id required")
        return value
