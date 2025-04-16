from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest
import weaviate.classes as wvc

from weaviate_agents.personalization.classes import (
    PersonalizationRequest,
    PersonalizedQueryResponse,
)
from weaviate_agents.personalization.query import PersonalizedQuery


def test_near_text(mock_httpx: Mock, personalization_request: PersonalizationRequest):
    query = PersonalizedQuery(
        agents_host="http://dummy-agent",
        headers={},
        persona_id=uuid4(),
        personalization_request=personalization_request,
    )
    output = query.near_text(
        query="Test query!",
        move_to=wvc.query.Move(force=1.5, concepts=["Towards me..."]),
        filters=wvc.query.Filter.all_of(
            [
                wvc.query.Filter.by_property("genre").equal("horror"),
                wvc.query.Filter.by_property("year").greater_or_equal("2000"),
            ]
        ),
        return_metadata=wvc.query.MetadataQuery.full(),
    )
    assert isinstance(output, PersonalizedQueryResponse)
    assert output.model_dump(mode="json") == MOCK_RESPONSE

    mock_httpx.post.assert_called_once()
    request_json = mock_httpx.post.call_args.kwargs["json"]
    request_params = request_json["query_request"]["query_parameters"]
    assert request_params["query_method"] == "near_text"


def test_bm25(mock_httpx: Mock, personalization_request: PersonalizationRequest):
    query = PersonalizedQuery(
        agents_host="http://dummy-agent",
        headers={},
        persona_id=uuid4(),
        personalization_request=personalization_request,
    )
    output = query.bm25(
        query="Test query!",
        filters=wvc.query.Filter.all_of(
            [
                wvc.query.Filter.by_property("genre").equal("horror"),
                wvc.query.Filter.by_property("year").greater_or_equal("2000"),
            ]
        ),
        return_metadata=wvc.query.MetadataQuery.full(),
    )
    assert isinstance(output, PersonalizedQueryResponse)
    assert output.model_dump(mode="json") == MOCK_RESPONSE

    mock_httpx.post.assert_called_once()
    request_json = mock_httpx.post.call_args.kwargs["json"]
    request_params = request_json["query_request"]["query_parameters"]
    assert request_params["query_method"] == "bm25"


def test_hybrid(mock_httpx: Mock, personalization_request: PersonalizationRequest):
    query = PersonalizedQuery(
        agents_host="http://dummy-agent",
        headers={},
        persona_id=uuid4(),
        personalization_request=personalization_request,
    )
    output = query.hybrid(
        query="Test query!",
        filters=wvc.query.Filter.all_of(
            [
                wvc.query.Filter.by_property("genre").equal("horror"),
                wvc.query.Filter.by_property("year").greater_or_equal("2000"),
            ]
        ),
        return_metadata=wvc.query.MetadataQuery.full(),
        vector=wvc.query.HybridVector.near_text(
            "Vector query?!",
            move_away=wvc.query.Move(force=1.5, concepts=["Not this way!"]),
        ),
    )
    assert isinstance(output, PersonalizedQueryResponse)
    assert output.model_dump(mode="json") == MOCK_RESPONSE

    mock_httpx.post.assert_called_once()
    request_json = mock_httpx.post.call_args.kwargs["json"]
    request_params = request_json["query_request"]["query_parameters"]
    assert request_params["query_method"] == "hybrid"


@pytest.fixture()
def mock_httpx(monkeypatch):
    mock = Mock()
    mock.post.return_value = httpx.Response(
        status_code=200,
        request=httpx.Request("post", "http://dummy-agent"),
        json=MOCK_RESPONSE,
    )
    monkeypatch.setattr("weaviate_agents.personalization.query.httpx", mock)
    return mock


@pytest.fixture()
def personalization_request():
    return PersonalizationRequest(
        collection_name="collection",
        create=False,
    )


MOCK_RESPONSE = {
    "objects": [
        {
            "uuid": "eba77486-3376-4d38-8fde-bfe978eaf4d4",
            "metadata": {
                "creation_time": None,
                "last_update_time": None,
                "distance": None,
                "certainty": None,
                "score": None,
                "explain_score": None,
                "is_consistent": None,
                "rerank_score": None,
            },
            "properties": {
                "title": "Avatar",
            },
            "references": None,
            "vector": {},
            "collection": "Movies",
        },
        {
            "uuid": "418691ee-241e-4671-9960-001bada94263",
            "metadata": {
                "creation_time": None,
                "last_update_time": None,
                "distance": None,
                "certainty": None,
                "score": None,
                "explain_score": None,
                "is_consistent": None,
                "rerank_score": None,
            },
            "properties": {
                "title": "Pandora",
                "vote_count": 0,
            },
            "references": None,
            "vector": {},
            "collection": "Movies",
        },
    ],
    "usage": {
        "requests": 0,
        "request_tokens": 0,
        "response_tokens": 0,
        "total_tokens": 0,
        "details": None,
    },
}
