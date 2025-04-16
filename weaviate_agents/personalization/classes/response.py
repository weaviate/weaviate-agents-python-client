from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator
from weaviate.collections.classes.internal import MetadataReturn
from weaviate.outputs.query import Object, QueryReturn

from weaviate_agents.classes.core import Usage


class PersonalizedObject(BaseModel):
    uuid: UUID
    original_rank: int
    personalized_rank: Optional[int]
    properties: Dict[str, Any]

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "uuid" in data:
            data["uuid"] = str(data["uuid"])
        return data


class PersonalizationAgentGetObjectsResponse(BaseModel):
    objects: list[PersonalizedObject]
    ranking_rationale: Optional[str] = None
    usage: Usage


class PersonalizedQueryResponse(BaseModel, QueryReturn):
    usage: Usage

    @field_validator("objects", mode="after")
    @classmethod
    def _ensure_metadata_type(cls, objects: list[Object]) -> list[Object]:
        for i in range(len(objects)):
            if isinstance(existing_metadata := objects[i].metadata, dict):
                objects[i].metadata = MetadataReturn(**existing_metadata)
        return objects
