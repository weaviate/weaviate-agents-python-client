from typing import Union

from pydantic import BaseModel


class QueryAgentCollectionConfig(BaseModel):
    """A collection configuration for the QueryAgent.

    Attributes:
        name: The name of the collection to query.
        view_properties: Optional list of property names the agent has the ability to view
            for this specific collection.
        target_vector: Optional target vector name(s) for collections with named vectors.
            Can be a single vector name or a list of vector names.
    """

    name: str
    view_properties: Union[list[str], None] = None
    target_vector: Union[str, list[str], None] = None
