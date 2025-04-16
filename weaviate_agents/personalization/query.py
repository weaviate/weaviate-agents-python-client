from typing import Any, List, Optional, Union
from uuid import UUID

import httpx
from weaviate.classes.query import Move, Rerank
from weaviate.collections.classes.filters import _Filters
from weaviate.collections.classes.grpc import (
    METADATA,
    HybridFusion,
    HybridVectorType,
    TargetVectorJoinType,
)
from weaviate.collections.classes.internal import ReturnProperties, ReturnReferences

from weaviate_agents.personalization.classes import (
    BM25QueryParameters,
    HybridQueryParameters,
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

    def near_text(
        self,
        query: Union[List[str], str],
        *,
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
        return_references: Optional[ReturnReferences[dict]] = None,
    ) -> PersonalizedQueryResponse:
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
            return_references=return_references,
        )
        return self._get_query_response(query_parameters)

    def bm25(
        self,
        query: Optional[str],
        *,
        query_properties: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        auto_limit: Optional[int] = None,
        filters: Optional[_Filters] = None,
        # group_by,
        rerank: Optional[Rerank] = None,
        include_vector: Union[bool, str, List[str]] = False,
        return_metadata: Optional[METADATA] = None,
        return_properties: Optional[ReturnProperties[dict]] = None,
        return_references: Optional[ReturnReferences[dict]] = None,
    ) -> PersonalizedQueryResponse:
        query_parameters = BM25QueryParameters(
            query=query,
            query_properties=query_properties,
            limit=limit,
            offset=offset,
            auto_limit=auto_limit,
            filters=filters,
            rerank=rerank,
            include_vector=include_vector,
            return_metadata=return_metadata,
            return_properties=return_properties,
            return_references=return_references,
        )
        return self._get_query_response(query_parameters)

    def hybrid(
        self,
        query: Optional[str],
        *,
        alpha: Union[int, float] = 0.7,
        vector: Optional[HybridVectorType] = None,
        query_properties: Optional[List[str]] = None,
        fusion_type: Optional[HybridFusion] = None,
        max_vector_distance: Optional[Union[int, float]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        auto_limit: Optional[int] = None,
        filters: Optional[_Filters] = None,
        # group_by,
        rerank: Optional[Rerank] = None,
        target_vector: Optional[TargetVectorJoinType] = None,
        include_vector: Union[bool, str, List[str]] = False,
        return_metadata: Optional[METADATA] = None,
        return_properties: Optional[ReturnProperties[dict]] = None,
        return_references: Optional[ReturnReferences[dict]] = None,
    ) -> PersonalizedQueryResponse:
        query_parameters = HybridQueryParameters(
            query=query,
            alpha=alpha,
            vector=vector,
            query_properties=query_properties,
            fusion_type=fusion_type,
            max_vector_distance=max_vector_distance,
            limit=limit,
            offset=offset,
            auto_limit=auto_limit,
            filters=filters,
            rerank=rerank,
            target_vector=target_vector,
            include_vector=include_vector,
            return_metadata=return_metadata,
            return_properties=return_properties,
            return_references=return_references,
        )
        return self._get_query_response(query_parameters)

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

    def _get_query_response(
        self, query_parameters: QueryParameters
    ) -> PersonalizedQueryResponse:
        response = httpx.post(
            self._route,
            headers=self._headers,
            json=self._get_request_data(query_parameters),
            timeout=self.timeout,
        )
        if response.is_error:
            raise Exception(response.text)

        return PersonalizedQueryResponse.model_validate(response.json())
