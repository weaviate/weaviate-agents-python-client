from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict
from typing_extensions import TypedDict

from weaviate_agents.query.classes import QueryAgentCollectionConfig
from weaviate_agents.query.classes.response import QueryResultWithCollectionNormalized


class SearchModeRequestBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    headers: dict[str, str]
    original_query: Union[str, ConversationContext]
    collections: list[Union[str, QueryAgentCollectionConfig]]
    limit: int
    offset: int


class SearchModeExecutionRequest(SearchModeRequestBase):
    searches: list[QueryResultWithCollectionNormalized]


class SearchModeGenerationRequest(SearchModeRequestBase):
    searches: None = None
    system_prompt: Optional[str] = None


class ChatMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class ConversationContext(BaseModel):
    messages: list[ChatMessage]
