from typing import Annotated, Union

from pydantic import BaseModel, ConfigDict
from weaviate.collections.classes.filters import _Filters

from weaviate_agents.serialise import serialise_filter


class QueryAgentCollectionConfig(BaseModel):
    """A collection configuration for the QueryAgent.

    Attributes:
        name: The name of the collection to query.
        tenant: Tenant name for collections with multi-tenancy enabled.
        view_properties: Optional list of property names the agent has the ability to view
            for this specific collection.
        target_vector: Optional target vector name(s) for collections with named vectors.
            Can be a single vector name or a list of vector names.
        additional_filters: Optional filters to apply when the query is executed, in addition
            to filters selected by the Query Agent (i.e., there are AND combined).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    tenant: Union[str, None] = None
    view_properties: Union[list[str], None] = None
    target_vector: Union[str, list[str], None] = None
    additional_filters: Union[Annotated[_Filters, serialise_filter], None] = None
