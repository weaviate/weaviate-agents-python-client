from typing import Annotated, List, Literal, Optional, Union
from typing_extensions import TypedDict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PlainSerializer, Field
from weaviate.classes.query import Move


class MoveSerialise(TypedDict):
    force: float
    objects: Optional[List[str]]
    concepts: Optional[List[str]]


def _serialise_move(move: Move) -> MoveSerialise:
    return MoveSerialise(
        force=move.force, objects=move._objects_list, concepts=move._concepts_list
    )


class NearTextQueryParameters(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    query_method: Literal["near_text"] = "near_text"

    query: Union[List[str], str]
    certainty: Union[int, float, None] = None
    distance: Union[int, float, None] = None
    move_to: Optional[Annotated[Move, PlainSerializer(_serialise_move)]] = None
    move_away: Optional[Annotated[Move, PlainSerializer(_serialise_move)]] = None
    limit: Union[int, None] = None
    offset: Union[int, None] = None
    auto_limit: Union[int, None] = None
    # filters: Optional[weaviate.collections.classes.filters._Filters] = None
    # group_by: Optional[weaviate.collections.classes.grpc.GroupBy] = None
    # rerank: Optional[weaviate.collections.classes.grpc.Rerank] = None
    # target_vector: Union[str, List[str], weaviate.collections.classes.grpc._MultiTargetVectorJoin, NoneType] = None
    include_vector: Union[bool, str, List[str]] = False
    # return_metadata: Union[List[Literal['creation_time', 'last_update_time', 'distance', 'certainty', 'score', 'explain_score', 'is_consistent']], weaviate.collections.classes.grpc.MetadataQuery, NoneType] = None
    # return_properties: Union[Sequence[Union[str, weaviate.collections.classes.grpc.QueryNested]], str, weaviate.collections.classes.grpc.QueryNested, bool, Type[~TProperties], NoneType] = None,
    # return_references: Union[weaviate.collections.classes.grpc._QueryReference, Sequence[weaviate.collections.classes.grpc._QueryReference], Type[~TReferences], NoneType] = None,


class BM25QueryParameters(BaseModel):
    query_method: Literal["bm25"] = "bm25"

    query: Union[str, None]
    query_properties: Union[List[str], None] = None
    limit: Union[int, None] = None
    offset: Union[int, None] = None
    auto_limit: Union[int, None] = None
    # filters: Optional[weaviate.collections.classes.filters._Filters] = None,
    # group_by: Optional[weaviate.collections.classes.grpc.GroupBy] = None,
    # rerank: Optional[weaviate.collections.classes.grpc.Rerank] = None,
    include_vector: Union[bool, str, List[str]] = False
    # return_metadata: Union[List[Literal['creation_time', 'last_update_time', 'distance', 'certainty', 'score', 'explain_score', 'is_consistent']], weaviate.collections.classes.grpc.MetadataQuery, NoneType] = None,
    # return_properties: Union[Sequence[Union[str, weaviate.collections.classes.grpc.QueryNested]], str, weaviate.collections.classes.grpc.QueryNested, bool, Type[~TProperties], NoneType] = None,
    # return_references: Union[weaviate.collections.classes.grpc._QueryReference, Sequence[weaviate.collections.classes.grpc._QueryReference], Type[~TReferences], NoneType] = None,


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
    # filters: Optional[weaviate.collections.classes.filters._Filters] = None,
    # group_by: Optional[weaviate.collections.classes.grpc.GroupBy] = None,
    # rerank: Optional[weaviate.collections.classes.grpc.Rerank] = None,
    # target_vector: Union[str, List[str], weaviate.collections.classes.grpc._MultiTargetVectorJoin, NoneType] = None,
    include_vector: Union[bool, str, List[str]] = False
    # return_metadata: Union[List[Literal['creation_time', 'last_update_time', 'distance', 'certainty', 'score', 'explain_score', 'is_consistent']], weaviate.collections.classes.grpc.MetadataQuery, NoneType] = None,
    # return_properties: Union[Sequence[Union[str, weaviate.collections.classes.grpc.QueryNested]], str, weaviate.collections.classes.grpc.QueryNested, bool, Type[~TProperties], NoneType] = None,
    # return_references: Union[weaviate.collections.classes.grpc._QueryReference, Sequence[weaviate.collections.classes.grpc._QueryReference], Type[~TReferences], NoneType] = None,


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
