from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer
from typing_extensions import TypedDict
from weaviate.classes.query import Move, Rerank
from weaviate.collections.classes.filters import (
    _FilterAnd,
    _FilterOr,
    _Filters,
    _FilterValue,
)
from weaviate.collections.classes.grpc import METADATA, TargetVectorJoinType
from weaviate.collections.classes.internal import ReturnProperties, ReturnReferences


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
    query_method: Literal["hybrid"] = "hybrid"

    query: Union[str, None]
    alpha: Union[int, float] = 0.7
    # vector: Union[Sequence[Union[int, float]], Sequence[Sequence[Union[int, float]]], Mapping[str, Union[Sequence[Union[int, float]], Sequence[Sequence[Union[int, float]]], weaviate.collections.classes.grpc._ListOfVectorsQuery[Sequence[Union[int, float]]], weaviate.collections.classes.grpc._ListOfVectorsQuery[Sequence[Sequence[Union[int, float]]]]]], weaviate.collections.classes.grpc._HybridNearText, weaviate.collections.classes.grpc._HybridNearVector, NoneType] = None
    query_properties: Union[List[str], None] = None
    # fusion_type: Optional[weaviate.collections.classes.grpc.HybridFusion] = None
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


class _MoveSerialise(TypedDict):
    force: float
    objects: Optional[List[str]]
    concepts: Optional[List[str]]


@PlainSerializer
def serialise_move(move: Move) -> _MoveSerialise:
    return _MoveSerialise(
        force=move.force, objects=move._objects_list, concepts=move._concepts_list
    )


class _FilterAndOrSerialise(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    combine: Literal["and", "or"]
    filters: list[_Filters]


@PlainSerializer
def serialise_filter(
    filter_and_or_value: Union[_FilterAnd, _FilterOr, _FilterValue],
) -> Union[_FilterValue, _FilterAndOrSerialise]:
    if isinstance(filter_and_or_value, _FilterValue):
        return filter_and_or_value

    if isinstance(filter_and_or_value, _FilterAnd):
        combine: Literal["and", "or"] = "and"
    elif isinstance(filter_and_or_value, _FilterOr):
        combine = "or"
    else:
        raise TypeError(f"Unknown filter type {type(filter_and_or_value)}")
    return _FilterAndOrSerialise(combine=combine, filters=filter_and_or_value.filters)
