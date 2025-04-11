from typing import Annotated

import pytest
from pydantic import BaseModel, ConfigDict
from weaviate.collections.classes.grpc import (
    HybridVectorType,
    _HybridNearText,
    _HybridNearVector,
    Move,
)

from weaviate_agents.personalization.classes.query import (
    serialise_hybrid_vector_type,
    serialise_move,
)


def test_serialise_move():
    class TestModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        field: Annotated[Move, serialise_move]

    model = TestModel(field=Move(force=1, concepts=["ooh go this way"]))
    serialised = model.model_dump(mode="json")

    expect = {"field": {"force": 1, "concepts": ["ooh go this way"], "objects": None}}
    assert serialised == expect


@pytest.mark.parametrize(
    "field, expect",
    [
        (
            _HybridNearText(text="aaaa", move_to=Move(force=1, concepts=["aa"])),
            {
                "field": {
                    "distance": None,
                    "certainty": None,
                    "text": "aaaa",
                    "move_to": {"force": 1.0, "objects": None, "concepts": ["aa"]},
                    "move_away": None,
                    "serialised_class": "_HybridNearText",
                }
            },
        ),
        (
            _HybridNearVector(vector=[1, 2, 3], distance=0.5),
            {
                "field": {
                    "serialised_class": "_HybridNearVector",
                    "vector": [1, 2, 3],
                    "distance": 0.5,
                    "certainty": None,
                }
            },
        ),
        ([1, 2, 3], {"field": [1, 2, 3]}),
        ([[1, 2, 3]], {"field": [[1, 2, 3]]}),
    ],
)
def test_serialise_hybrid_vector_type(field: HybridVectorType, expect: dict):
    class TestModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        field: Annotated[HybridVectorType, serialise_hybrid_vector_type]

    model = TestModel(field=field)
    serialised = model.model_dump(mode="json")
    assert serialised == expect
