from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, PlainSerializer
from typing_extensions import TypedDict
from weaviate.classes.query import Move
from weaviate.collections.classes.filters import (
    _FilterAnd,
    _FilterOr,
    _Filters,
    _FilterValue,
)
from weaviate.collections.classes.grpc import (
    HybridVectorType,
    NearVectorInputType,
    _HybridNearText,
    _HybridNearVector,
)


class _MoveSerialise(TypedDict):
    force: float
    objects: Optional[List[str]]
    concepts: Optional[List[str]]


@PlainSerializer
def serialise_move(move: Optional[Move]) -> Optional[_MoveSerialise]:
    if move is None:
        return None
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


# A set of models to help serialise HybridVectorType, which is a union of
# NearVectorInputType (itself a union over std types), _HybridNearText and _HybridNearVector.
class _HybridNearTextSerialise(_HybridNearText):
    serialised_class: Literal["_HybridNearText"] = "_HybridNearText"

    move_to: Annotated[Optional[Move], serialise_move] = None
    move_away: Annotated[Optional[Move], serialise_move] = None


def _serialise_hybrid_near_text(model: _HybridNearText) -> _HybridNearTextSerialise:
    return _HybridNearTextSerialise.model_validate(model.model_dump())


class _HybridNearVectorSerialise(BaseModel):
    serialised_class: Literal["_HybridNearVector"] = "_HybridNearVector"

    vector: NearVectorInputType
    distance: Optional[float]
    certainty: Optional[float]


def _serialise_hybrid_near_vector(
    model: _HybridNearVector,
) -> _HybridNearVectorSerialise:
    return _HybridNearVectorSerialise(
        vector=model.vector,
        distance=model.distance,
        certainty=model.certainty,
    )


@PlainSerializer
def serialise_hybrid_vector_type(
    vector: HybridVectorType,
) -> Union[_HybridNearTextSerialise, _HybridNearVectorSerialise, NearVectorInputType]:
    if isinstance(vector, _HybridNearText):
        return _serialise_hybrid_near_text(vector)
    elif isinstance(vector, _HybridNearVector):
        return _serialise_hybrid_near_vector(vector)
    else:
        return vector
