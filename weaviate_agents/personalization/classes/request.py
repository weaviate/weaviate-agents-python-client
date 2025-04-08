from typing import Dict, Union
from pydantic import BaseModel


class PersonalizationRequest(BaseModel):
    collection_name: str
    create: bool = True
    headers: Union[Dict[str, str], None] = None
    persona_properties: Union[Dict[str, str], None]= None
    item_collection_vector_name: Union[str, None] = None
