from datetime import datetime, timezone
from typing import Annotated

import pytest
from pydantic import BaseModel, ConfigDict
from weaviate.collections.classes.filters import Filter, _Filters
from weaviate.collections.classes.grpc import (
    HybridVector,
    HybridVectorType,
    Move,
)

from weaviate_agents.serialise import (
    serialise_filter,
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
            Filter.by_property("Property").equal("This Value"),
            {
                "field": {
                    "operator": "Equal",
                    "target": "Property",
                    "value": "This Value",
                }
            },
        ),
        (
            (
                Filter.by_property("Property").equal("This Value...")
                & Filter.by_property("Property").equal("... and this one!")
            ),
            {
                "field": {
                    "combine": "and",
                    "filters": [
                        {
                            "operator": "Equal",
                            "target": "Property",
                            "value": "This Value...",
                        },
                        {
                            "operator": "Equal",
                            "target": "Property",
                            "value": "... and this one!",
                        },
                    ],
                },
            },
        ),
        (
            (
                Filter.by_property("Property").equal("This Value...")
                | Filter.by_property("Property").equal("... or this one?")
            ),
            {
                "field": {
                    "combine": "or",
                    "filters": [
                        {
                            "operator": "Equal",
                            "target": "Property",
                            "value": "This Value...",
                        },
                        {
                            "operator": "Equal",
                            "target": "Property",
                            "value": "... or this one?",
                        },
                    ],
                },
            },
        ),
        (
            (
                (
                    Filter.by_property("prop_str").equal("a")
                    | Filter.by_property("prop_str").equal("b")
                )
                & Filter.by_property("prop_int").greater_than("c")
            ),
            {
                "field": {
                    "combine": "and",
                    "filters": [
                        {
                            "combine": "or",
                            "filters": [
                                {
                                    "operator": "Equal",
                                    "target": "prop_str",
                                    "value": "a",
                                },
                                {
                                    "operator": "Equal",
                                    "target": "prop_str",
                                    "value": "b",
                                },
                            ],
                        },
                        {
                            "operator": "GreaterThan",
                            "target": "prop_int",
                            "value": "c",
                        },
                    ],
                },
            },
        ),
        (
            (
                (
                    (
                        Filter.by_property("prop_str_1").equal("a")
                        | Filter.by_property("prop_str_1").equal("b")
                    )
                    & (
                        Filter.by_property("prop_str_2").equal("c")
                        | Filter.by_property("prop_str_2").equal("d")
                    )
                )
                & (
                    (
                        Filter.by_property("prop_int").greater_than(1)
                        | Filter.by_property("prop_int").less_than(-1)
                    )
                    & (
                        (
                            Filter.by_property("prop_str_3").like("*hello*")
                            & Filter.by_property("prop_str_3").like("*world*")
                        )
                        | (
                            Filter.by_creation_time().less_than(
                                datetime.fromtimestamp(1757669274, tz=timezone.utc)
                            )
                            | Filter.by_update_time().greater_than(
                                datetime.fromtimestamp(1757669274, tz=timezone.utc)
                            )
                        )
                    )
                )
            ),
            {
                "field": {
                    "combine": "and",
                    "filters": [
                        {
                            "combine": "and",
                            "filters": [
                                {
                                    "combine": "or",
                                    "filters": [
                                        {
                                            "operator": "Equal",
                                            "target": "prop_str_1",
                                            "value": "a",
                                        },
                                        {
                                            "operator": "Equal",
                                            "target": "prop_str_1",
                                            "value": "b",
                                        },
                                    ],
                                },
                                {
                                    "combine": "or",
                                    "filters": [
                                        {
                                            "operator": "Equal",
                                            "target": "prop_str_2",
                                            "value": "c",
                                        },
                                        {
                                            "operator": "Equal",
                                            "target": "prop_str_2",
                                            "value": "d",
                                        },
                                    ],
                                },
                            ],
                        },
                        {
                            "combine": "and",
                            "filters": [
                                {
                                    "combine": "or",
                                    "filters": [
                                        {
                                            "operator": "GreaterThan",
                                            "target": "prop_int",
                                            "value": 1,
                                        },
                                        {
                                            "operator": "LessThan",
                                            "target": "prop_int",
                                            "value": -1,
                                        },
                                    ],
                                },
                                {
                                    "combine": "or",
                                    "filters": [
                                        {
                                            "combine": "and",
                                            "filters": [
                                                {
                                                    "operator": "Like",
                                                    "target": "prop_str_3",
                                                    "value": "*hello*",
                                                },
                                                {
                                                    "operator": "Like",
                                                    "target": "prop_str_3",
                                                    "value": "*world*",
                                                },
                                            ],
                                        },
                                        {
                                            "combine": "or",
                                            "filters": [
                                                {
                                                    "operator": "LessThan",
                                                    "target": "_creationTimeUnix",
                                                    "value": "2025-09-12T09:27:54Z",
                                                },
                                                {
                                                    "operator": "GreaterThan",
                                                    "target": "_lastUpdateTimeUnix",
                                                    "value": "2025-09-12T09:27:54Z",
                                                },
                                            ],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            },
        ),
    ],
)
def test_serialise_filter(field, expect):
    class TestModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        field: Annotated[_Filters, serialise_filter]

    model = TestModel(field=field)
    serialised = model.model_dump(mode="json")
    assert serialised == expect


@pytest.mark.parametrize(
    "field, expect",
    [
        (
            HybridVector.near_text(
                query="aaaa", move_to=Move(force=1, concepts=["aa"])
            ),
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
            HybridVector.near_vector(vector=[1, 2, 3], distance=0.5),
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
