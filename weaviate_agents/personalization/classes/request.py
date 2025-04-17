from typing import Annotated, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from weaviate.collections.classes.filters import _Filters

from weaviate_agents.personalization.classes.query import serialise_filter


class PersonalizationRequest(BaseModel):
    collection_name: str
    create: bool = True
    headers: Union[Dict[str, str], None] = None
    persona_properties: Union[Dict[str, str], None] = None
    item_collection_vector_name: Union[str, None] = None


class GetObjectsRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    persona_id: UUID
    limit: int = 10
    recent_interactions_count: int = 100
    exclude_interacted_items: bool = True
    decay_rate: float = 0.1
    exclude_items: List[str] = []
    use_agent_ranking: bool = True
    explain_results: bool = True
    instruction: Optional[str] = None
    filters: Optional[Annotated[_Filters, serialise_filter]] = None
