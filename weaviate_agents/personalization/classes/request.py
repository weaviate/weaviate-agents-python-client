from typing import Dict, Union

from pydantic import BaseModel

from weaviate_agents.personalization.classes.query import serialise_filter

class PersonalizationRequest(BaseModel):
    collection_name: str
    create: bool = True
    headers: Union[Dict[str, str], None] = None
    persona_properties: Union[Dict[str, str], None] = None
    item_collection_vector_name: Union[str, None] = None


class GetObjectsRequest(BaseModel):
    pass
