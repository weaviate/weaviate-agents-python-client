from typing import Dict, Union

from pydantic import BaseModel


class Usage(BaseModel):
    requests: Union[int, str] = 0
    request_tokens: Union[int, str, None] = None
    response_tokens: Union[int, str, None] = None
    total_tokens: Union[int, str, None] = None
    details: Union[Dict[str, int], Dict[str, str], None] = None
