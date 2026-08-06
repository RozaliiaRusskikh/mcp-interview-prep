from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatRequest(CamelModel):
    question: str = Field(min_length=1, max_length=500)


class ChatResponse(CamelModel):
    answer: str
    source: Literal["deterministic", "llm", "rate_capped"]
