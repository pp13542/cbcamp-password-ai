"""Pydantic request and response schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def reject_blank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value.strip()


class ChatResponse(BaseModel):
    answer: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    adapter_loaded: bool
    model_name: str
    device: str
    emergency_stable_mode: bool

