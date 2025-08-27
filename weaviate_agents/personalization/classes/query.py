from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from weaviate.classes.query import Move, Rerank
from weaviate.collections.classes.filters import _Filters
from weaviate.collections.classes.grpc import (
    METADATA,
    HybridFusion,
    HybridVectorType,
    TargetVectorJoinType,
)
from weaviate.collections.classes.internal import ReturnProperties, ReturnReferences

from weaviate_agents.serialise import (
    serialise_filter,
    serialise_hybrid_vector_type,
    serialise_move,
)


class NearTextQueryParameters(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    query_method: Literal["near_text"] = "near_text"

    query: Union[List[str], str]
    certainty: Union[int, float, None] = None
    distance: Union[int, float, None] = None
    move_to: Optional[Annotated[Move, serialise_move]] = None
    move_away: Optional[Annotated[Move, serialise_move]] = None
    limit: Union[int, None] = None
    offset: Union[int, None] = None
    auto_limit: Union[int, None] = None
    filters: Optional[Annotated[_Filters, serialise_filter]] = None
    # group_by: Optional[weaviate.collections.classes.grpc.GroupBy] = None
    rerank: Optional[Rerank] = None
    target_vector: Optional[TargetVectorJoinType] = None
    include_vector: Union[bool, str, List[str]] = False
    return_metadata: Optional[METADATA] = None
    return_properties: Optional[ReturnProperties[dict]] = None
    return_references: Optional[ReturnReferences[dict]] = None


class BM25QueryParameters(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    query_method: Literal["bm25"] = "bm25"

    query: Union[str, None]
    query_properties: Union[List[str], None] = None
    limit: Union[int, None] = None
    offset: Union[int, None] = None
    auto_limit: Union[int, None] = None
    filters: Optional[Annotated[_Filters, serialise_filter]] = None
    # group_by: Optional[weaviate.collections.classes.grpc.GroupBy] = None,
    rerank: Optional[Rerank] = None
    include_vector: Union[bool, str, List[str]] = False
    return_metadata: Optional[METADATA] = None
    return_properties: Optional[ReturnProperties[dict]] = None
    return_references: Optional[ReturnReferences[dict]] = None


class HybridQueryParameters(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    query_method: Literal["hybrid"] = "hybrid"

    query: Union[str, None]
    alpha: Union[int, float] = 0.7
    vector: Union[Annotated[HybridVectorType, serialise_hybrid_vector_type], None] = (
        None
    )
    query_properties: Union[List[str], None] = None
    fusion_type: Optional[HybridFusion] = None
    max_vector_distance: Union[int, float, None] = None
    limit: Union[int, None] = None
    offset: Union[int, None] = None
    auto_limit: Union[int, None] = None
    filters: Optional[Annotated[_Filters, serialise_filter]] = None
    # group_by: Optional[weaviate.collections.classes.grpc.GroupBy] = None,
    rerank: Optional[Rerank] = None
    target_vector: Optional[TargetVectorJoinType] = None
    include_vector: Union[bool, str, List[str]] = False
    return_metadata: Optional[METADATA] = None
    return_properties: Optional[ReturnProperties[dict]] = None
    return_references: Optional[ReturnReferences[dict]] = None


QueryParameters = Union[
    NearTextQueryParameters, BM25QueryParameters, HybridQueryParameters
]


class QueryRequest(BaseModel):
    persona_id: UUID
    strength: float
    recent_interactions_count: int
    decay_rate: float
    overfetch_factor: float
    query_parameters: QueryParameters = Field(discriminator="query_method")
