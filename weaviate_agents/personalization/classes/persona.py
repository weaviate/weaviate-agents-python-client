from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Persona(BaseModel):
    id: UUID
    properties: Dict[str, Any]

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "id" in data:
            data["id"] = str(data["id"])
        return data


class PersonaInteraction(BaseModel):
    """Interaction between a persona and an item.

    If `replace_previous_interactions` is `True`, the interaction history for that specific
    item and persona pair will be replaced with the new interaction.
    """

    id: UUID
    item_id: UUID
    weight: float
    replace_previous_interactions: bool = False
    created_at: Optional[datetime] = None

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "id" in data:
            data["id"] = str(data["id"])
        if "item_id" in data:
            data["item_id"] = str(data["item_id"])
        if "created_at" in data and data["created_at"] is not None:
            data["created_at"] = data["created_at"].isoformat()
        return data


class PersonaInteractionResponse(BaseModel):
    """Response model for persona interactions when retrieving them."""

    item_id: UUID = Field(alias="uuid")
    weight: float
    created_at: str = Field(alias="createdAt")

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "item_id" in data:
            data["item_id"] = str(data["item_id"])
        if "created_at" in data:
            data["created_at"] = data["created_at"].isoformat()
        return data
