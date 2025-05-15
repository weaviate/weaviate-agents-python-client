import httpx
import pytest
from pydantic import ValidationError

from weaviate_agents.classes.query import QueryAgentCollectionConfig, QueryAgentResponse
from weaviate_agents.query import QueryAgent


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


class FakeResponse:
    """A fake HTTP response for testing purposes.

    Attributes:
        status_code (int): The HTTP status code.
        _json (dict): The JSON data to return.
    """

    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self.is_error = 400 <= status_code <= 599
        self._json = json_data
        self.text = json_data

    def json(self) -> dict:
        """Return the JSON data of the fake response.

        Returns:
            dict: The JSON data.
        """
        return self._json


def fake_post_success(*args, **kwargs) -> FakeResponse:
    """Simulate a successful HTTP POST response.

    Returns:
        FakeResponse: A fake HTTP response with status code 200.
    """
    json_data = {
        "original_query": "test query",
        "collection_names": ["test_collection"],
        "searches": [],
        "aggregations": [],
        "sources": [{"object_id": "123", "collection": "test_collection"}],
        "usage": {
            "requests": 1,
            "request_tokens": 10,
            "response_tokens": 20,
            "total_tokens": 30,
            "details": {},
        },
        "total_time": 0.1,
        "aggregation_answer": None,
        "has_aggregation_answer": False,
        "has_search_answer": False,
        "is_partial_answer": False,
        "missing_information": [],
        "final_answer": "final answer",
    }
    return FakeResponse(200, json_data)


def fake_post_failure(*args, **kwargs) -> FakeResponse:
    """Simulate a failed HTTP POST response.

    Returns:
        FakeResponse: A fake HTTP response with a non-200 status code.
    """
    json_data = {
        "error": {
            "message": "Test error message",
            "code": "test_error_code",
            "details": {"info": "test detail"},
        }
    }
    return FakeResponse(400, json_data)


def test_run_success(monkeypatch):
    """Test that QueryAgent.run returns a valid QueryAgentResponse when the HTTP call is successful.

    Returns:
        None.
    """
    monkeypatch.setattr(httpx, "post", fake_post_success)
    dummy_client = DummyClient()
    agent = QueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    result = agent.run("test query")
    assert isinstance(result, QueryAgentResponse)
    assert result.original_query == "test query"
    assert result.collection_names == ["test_collection"]
    assert result.total_time == 0.1
    assert result.final_answer == "final answer"


def test_run_failure(monkeypatch):
    """Test that QueryAgent.run raises an exception when the HTTP response indicates an error.

    Returns:
        None.
    """
    monkeypatch.setattr(httpx, "post", fake_post_failure)
    dummy_client = DummyClient()
    agent = QueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    with pytest.raises(Exception) as exc_info:
        agent.run("failure query")

    assert (
        str(exc_info.value)
        == "{'error': {'message': 'Test error message', 'code': 'test_error_code', 'details': {'info': 'test detail'}}}"
    )


def test_query_agent_response_model_validation():
    """Test that the QueryAgentResponse model raises a ValidationError when required fields are missing.

    Returns:
        None.
    """
    incomplete_data = {"original_query": "incomplete query"}
    with pytest.raises(ValidationError):
        QueryAgentResponse(**incomplete_data)


def test_run_with_target_vector(monkeypatch):
    """Test that QueryAgent.run correctly passes the target_vector argument in the request body."""
    captured = {}

    def fake_post_with_capture(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        # Return a normal successful response
        return fake_post_success()

    monkeypatch.setattr(httpx, "post", fake_post_with_capture)
    dummy_client = DummyClient()
    agent = QueryAgent(dummy_client, agents_host="http://dummy-agent")
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    # Test with single target vector
    result = agent.run(
        "test query",
        collections=[
            QueryAgentCollectionConfig(
                name="test_collection", target_vector="my_vector"
            )
        ],
    )
    assert isinstance(result, QueryAgentResponse)
    assert captured["json"]["collections"][0]["target_vector"] == "my_vector"

    # Test with multiple target vectors
    result = agent.run(
        "test query",
        collections=[
            QueryAgentCollectionConfig(
                name="test_collection", target_vector=["first_vector", "second_vector"]
            )
        ],
    )
    assert isinstance(result, QueryAgentResponse)
    assert captured["json"]["collections"][0]["target_vector"] == [
        "first_vector",
        "second_vector",
    ]
