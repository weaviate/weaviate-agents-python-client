from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, ConfigDict, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue, SkipJsonSchema
from pydantic_core import core_schema
from typing_extensions import Literal

IMAGE_KEYWORD = "X-query-agent-image"

ImageShape = Literal["square", "landscape", "portrait"]


class QAImage(BaseModel):
    model_config = ConfigDict(json_schema_extra={IMAGE_KEYWORD: True})

    image_prompt: str
    base64: SkipJsonSchema[str]  # hidden from the LLM's schema; server fills it


@dataclass(frozen=True)
class ImageOptions:
    shape: Optional[ImageShape] = None  # unset falls back to the backend default

    def __get_pydantic_json_schema__(
        self, core_schema_: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = handler(core_schema_)
        if self.shape is not None:
            schema["X-image-shape"] = self.shape
        return schema
