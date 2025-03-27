from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel


class Usage(BaseModel):
    requests: Union[int, str] = 0
    request_tokens: Union[int, str, None] = None
    response_tokens: Union[int, str, None] = None
    total_tokens: Union[int, str, None] = None
    details: Union[Dict[str, int], Dict[str, str], None] = None


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
