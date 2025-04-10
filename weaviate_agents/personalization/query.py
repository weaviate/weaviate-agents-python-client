from typing import Any, List, Optional, Union
from uuid import UUID

import httpx
from weaviate.classes.query import Move, Rerank
from weaviate.collections.classes.filters import _Filters
from weaviate.collections.classes.grpc import TargetVectorJoinType, METADATA
from weaviate.collections.classes.internal import ReturnProperties

from weaviate_agents.personalization.classes import (
    NearTextQueryParameters,
    PersonalizationRequest,
    PersonalizedQueryResponse,
    QueryParameters,
    QueryRequest,
)


class PersonalizedQuery:
    def __init__(
        self,
        agents_host: str,
        headers: dict,
        persona_id: UUID,
        personalization_request: PersonalizationRequest,
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

    def _get_request_data(self, query_parameters: QueryParameters) -> dict[str, Any]:
        query_request = QueryRequest.model_validate(
            {
                "persona_id": self.persona_id,
                "strength": self.strength,
                "recent_interactions_count": self.recent_interactions_count,
                "decay_rate": self.decay_rate,
                "overfetch_factor": self.overfetch_factor,
                "query_parameters": query_parameters,
            }
        )
        return {
            "query_request": query_request.model_dump(mode="json"),
            "personalization_request": self.personalization_request.model_dump(
                mode="json"
            ),
        }

    def near_text(
        self,
        query: Union[List[str], str],
        certainty: Union[int, float, None] = None,
        distance: Union[int, float, None] = None,
        move_to: Optional[Move] = None,
        move_away: Optional[Move] = None,
        limit: Union[int, None] = None,
        offset: Union[int, None] = None,
        auto_limit: Union[int, None] = None,
        filters: Optional[_Filters] = None,
        # group_by,
        rerank: Optional[Rerank] = None,
        target_vector: Optional[TargetVectorJoinType] = None,
        include_vector: Union[bool, str, List[str]] = False,
        return_metadata: Optional[METADATA] = None,
        return_properties: Optional[ReturnProperties[dict]] = None,
        # return_references,
    ):
        query_parameters = NearTextQueryParameters(
            query=query,
            certainty=certainty,
            distance=distance,
            move_to=move_to,
            move_away=move_away,
            limit=limit,
            offset=offset,
            auto_limit=auto_limit,
            filters=filters,
            rerank=rerank,
            target_vector=target_vector,
            include_vector=include_vector,
            return_metadata=return_metadata,
            return_properties=return_properties,
        )
        response = httpx.post(
            self._route,
            headers=self._headers,
            json=self._get_request_data(query_parameters),
            timeout=self.timeout,
        )
        response_data = response.raise_for_status().json()
        return PersonalizedQueryResponse.model_validate(response_data)
