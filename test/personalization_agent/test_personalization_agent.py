from unittest.mock import Mock
from uuid import UUID, uuid4

import httpx
import pytest
import weaviate.classes as wvc

from weaviate_agents.personalization.personalization_agent import (
    PersonalizationAgent,
    PersonalizationAgentGetObjectsResponse,
    PersonalizedQuery,
)


class DummyClient:
    """A dummy client to simulate the Weaviate client for testing purposes."""

    def __init__(self):
        self._connection = self  # Simulate connection
        self.url = "http://test-url:443"  # Add url attribute
        self.additional_headers = {"Authorization": "test-token"}

    def get_current_bearer_token(self) -> str:
        """Simulate bearer token retrieval from connection.

        Returns:
            str: The test bearer token prefixed with 'Bearer '.
        """
        return "Bearer test-token"


@pytest.fixture
def agent() -> PersonalizationAgent:
    return PersonalizationAgent(
        client=DummyClient(),  # type: ignore
        reference_collection="TestCollection",
    )


def test_query(agent: PersonalizationAgent):
    query = agent.query(persona_id=uuid4())
    assert isinstance(query, PersonalizedQuery)


@pytest.mark.parametrize(
    "filters, filter_request",
    [
        (None, None),
        (
            wvc.query.Filter.by_property("title").not_equal("Avatar"),
            {"operator": "NotEqual", "target": "title", "value": "Avatar"},
        ),
        (
            (
                wvc.query.Filter.by_property("title").not_equal("Avatar")
                & wvc.query.Filter.by_property("genres").not_equal("comedy")
            ),
            {
                "combine": "and",
                "filters": [
                    {"operator": "NotEqual", "target": "title", "value": "Avatar"},
                    {"operator": "NotEqual", "target": "genres", "value": "comedy"},
                ],
            },
        ),
    ],
)
def test_get_objects(agent: PersonalizationAgent, monkeypatch, filters, filter_request):
    mock_response = {
        "objects": [
            {
                "uuid": "ae0fc31d-2f11-4e3a-a0f8-6e64795d7db9",
                "original_rank": 0,
                "personalized_rank": None,
                "properties": {
                    "title": "The Crush",
                    "genres": ["Drama", "Thriller", "Horror"],
                },
            },
            {
                "uuid": "f557e407-74db-453a-95b4-9357045be38d",
                "original_rank": 1,
                "personalized_rank": None,
                "properties": {
                    "title": "Armed Response",
                    "genres": ["Action", "Horror", "Thriller"],
                },
            },
        ],
        "ranking_rationale": None,
        "usage": {
            "requests": 0,
            "request_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0,
            "details": None,
        },
    }

    mock_httpx = Mock()
    mock_httpx.post.return_value = httpx.Response(
        status_code=200,
        request=httpx.Request("post", "http://dummy-agent"),
        json=mock_response,
    )
    monkeypatch.setattr(
        "weaviate_agents.personalization.personalization_agent.httpx", mock_httpx
    )

    persona_id = UUID("32a31598-42a8-4ed2-92d0-1273c7dbdcb0")
    recommendations = agent.get_objects(
        persona_id=persona_id,
        filters=filters,
    )
    expected_request = {
        "objects_request": {
            "persona_id": "32a31598-42a8-4ed2-92d0-1273c7dbdcb0",
            "limit": 10,
            "recent_interactions_count": 100,
            "exclude_interacted_items": True,
            "decay_rate": 0.1,
            "exclude_items": [],
            "use_agent_ranking": True,
            "explain_results": True,
            "instruction": None,
            "filters": filter_request,
        },
        "personalization_request": {
            "collection_name": "TestCollection",
            "headers": {"Authorization": "test-token"},
            "item_collection_vector_name": None,
            "create": False,
        },
    }

    mock_httpx.post.assert_called_once()
    request_json = mock_httpx.post.call_args.kwargs["json"]
    assert request_json == expected_request

    assert isinstance(recommendations, PersonalizationAgentGetObjectsResponse)
    assert recommendations.model_dump(mode="json") == mock_response
