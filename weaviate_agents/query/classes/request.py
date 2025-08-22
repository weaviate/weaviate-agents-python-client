from typing import Optional, Union

from pydantic import BaseModel, ConfigDict

from weaviate_agents.query.classes import QueryAgentCollectionConfig
from weaviate_agents.query.classes.response import QueryResultWithCollection


class SearchModeRequestBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    headers: dict[str, str]
    original_query: str
    collections: list[Union[str, QueryAgentCollectionConfig]]
    limit: int
    offset: int


class SearchModeExecutionRequest(SearchModeRequestBase):
    searches: list[QueryResultWithCollection]


class SearchModeGenerationRequest(SearchModeRequestBase):
    searches: None = None
    system_prompt: Optional[str] = None
