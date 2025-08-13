from typing import Annotated, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict
from weaviate.collections.classes.filters import _Filters

from weaviate_agents.personalization.classes.query import serialise_filter  # TODO: move upwards

from weaviate_agents.query.classes import QueryAgentCollectionConfig
from weaviate_agents.query.classes.response import QueryResultWithCollection


class SearchModeRequestBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    original_query: str
    collections: list[Union[str, QueryAgentCollectionConfig]]
    limit: int
    offset: int
    # TODO: This will need to be modified as the type isn't really right, but it's currently what the backend expects
    user_filters: Optional[list[Annotated[_Filters, serialise_filter]]] = None


class SearchModeExecutionRequest(SearchModeRequestBase):
    searches: list[QueryResultWithCollection]


class SearchModeGenerationRequest(SearchModeRequestBase):
    searches: None = None
    system_prompt: Optional[str] = None
