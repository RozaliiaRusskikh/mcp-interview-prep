from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatMessage(CamelModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(CamelModel):
    question: str = Field(min_length=1, max_length=500)
    # Prior turns, oldest first — lets the LLM answer context-dependent
    # follow-ups (e.g. "yes" after it offers to elaborate). Capped well
    # under the Gemini free-tier daily budget this app already runs on.
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(CamelModel):
    answer: str
    source: Literal["deterministic", "llm", "rate_capped"]


class Situation(CamelModel):
    id: int
    category: str
    situation: str
    task: str
    action: str
    result: str


class Experience(CamelModel):
    title: str
    company: str
    dates: str
    highlights: list[str]


class Skill(CamelModel):
    skill: str
    category: str
    supporting_highlights: list[str]


class Contact(CamelModel):
    email: str
    phone: str
    linkedin: str
    github: str
    location: str
