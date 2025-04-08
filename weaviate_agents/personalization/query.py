from typing import Any, Optional
from uuid import UUID

import httpx


class PersonalizedQuery:
    def __init__(
        self,
        agents_host: str,
        headers: dict,
        persona_id: UUID,
        personalization_request: dict[str, Any],
        timeout: Optional[int] = None,
        strength: float = 1.1,
        overfetch_factor: float = 1.5,
        recent_interactions_count: int = 100,
        decay_rate: float = 0.1,
    ):
        self._route = f"{agents_host}/personalization/query"
        self._headers = headers
        self.persona_id = persona_id
        self.timeout = timeout

        self.personalization_request = personalization_request
        self.strength = strength
        self.overfetch_factor = overfetch_factor
        self.recent_interactions_count = recent_interactions_count
        self.decay_rate = decay_rate

    def _get_request_data(self, query_method: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "query_request": {
                "persona_id": str(self.persona_id),
                "strength": self.strength,
                "recent_interactions_count": self.recent_interactions_count,
                "decay_rate": self.decay_rate,
                "overfetch_factor": self.overfetch_factor,
                "query_parameters": {
                    "query_method": query_method,
                    **kwargs
                }
            },
            "personalization_request": self.personalization_request,
        }

    def near_text(
        self,
        **kwargs,  # TODO: Should match the collections.query.near_text(...) method
    ):
        request_data = self._get_request_data(
            query_method="near_text",
            **kwargs
        )
        response = httpx.post(
            self._route,
            headers=self._headers,
            json=request_data,
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError('...') from exc  # TODO

        return response.json()
