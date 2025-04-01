from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Persona(BaseModel):
    persona_id: UUID
    properties: Dict[str, Any]


class PersonaInteraction(BaseModel):
    """Interaction between a persona and an item.

    If `replace_previous_interactions` is `True`, the interaction history for that specific
    item and persona pair will be replaced with the new interaction.
    """

    persona_id: UUID
    item_id: UUID
    weight: float
    replace_previous_interactions: bool = False
    created_at: Optional[datetime] = None


class PersonaInteractionResponse(BaseModel):
    """Response model for persona interactions when retrieving them."""

    item_id: UUID = Field(alias="uuid")
    weight: float
    created_at: str = Field(alias="createdAt")
