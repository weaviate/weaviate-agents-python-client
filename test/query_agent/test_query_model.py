import json
from contextlib import asynccontextmanager, contextmanager

import httpx
import pytest
from httpx_sse import ServerSentEvent
from pydantic import ValidationError

from weaviate_agents.classes.query import (
    ProgressMessage,
    QueryAgentCollectionConfig,
    QueryAgentResponse,
    StreamedTokens,
)
from weaviate_agents.query import AsyncQueryAgent, QueryAgent


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


FAKE_SUCCESS_JSON = {
    "original_query": "test query",
    "collection_names": ["test_collection"],
    "searches": [
        [
            {
                "collection": "test_collection",
                "queries": ["Test query!"],
                "filters": [
                    [
                        {
                            "filter_type": "integer",
                            "property_name": "prop_int",
                            "operator": "=",
                            "value": 1.0,
                        },
                        {
                            "filter_type": "integer_array",
                            "property_name": "prop_int_aray",
                            "operator": "contains_all",
                            "value": [1.0, 2.0],
                        },
                        {
                            "filter_type": "text",
                            "property_name": "prop_text",
                            "operator": "LIKE",
                            "value": "*something*",
                        },
                        {
                            "filter_type": "text_array",
                            "property_name": "prop_text_array",
                            "operator": "contains_any",
                            "value": ["one", "two"],
                        },
                        {
                            "filter_type": "boolean",
                            "property_name": "prop_bool",
                            "operator": "=",
                            "value": True,
                        },
                        {
                            "filter_type": "boolean_array",
                            "property_name": "prop_bool_array",
                            "operator": "contains_any",
                            "value": [True, False],
                        },
                        {
                            "filter_type": "date_range",
                            "property_name": "prop_date",
                            "value": {
                                "date_from": "2025-01-01T12:01:23Z",
                                "date_to": "2025-01-02T12:01:23Z",
                                "inclusive_from": True,
                                "inclusive_to": True,
                            },
                        },
                        {
                            "filter_type": "date_range",
                            "property_name": "prop_date",
                            "value": {
                                "exact_timestamp": "2025-01-01T12:01:23Z",
                                "operator": "=",
                            },
                        },
                        {
                            "filter_type": "date_array",
                            "property_name": "prop_date_array",
                            "operator": "contains_all",
                            "value": [
                                "2025-01-01T12:01:23Z",
                                "2025-01-02T12:01:23Z",
                            ],
                        },
                        {
                            "filter_type": "geo",
                            "property_name": "prop_geo",
                            "latitude": 10.0,
                            "longitude": 20.0,
                            "max_distance_meters": 30.0,
                        },
                        {
                            "filter_type": "something_new",
                            "property_name": "strange_property",
                            "value": "xyz",
                        },
                    ]
                ],
                "filter_operators": "AND",
            },
            {
                "collection": "test_collection",
                "queries": [None],
                "filters": [
                    [
                        {
                            "filter_type": "integer",
                            "property_name": "prop_int",
                            "operator": "=",
                            "value": 1.0,
                        },
                        {
                            "filter_type": "integer_array",
                            "property_name": "prop_int_aray",
                            "operator": "contains_all",
                            "value": [1.0, 2.0],
                        },
                        {
                            "filter_type": "text",
                            "property_name": "prop_text",
                            "operator": "LIKE",
                            "value": "*something*",
                        },
                        {
                            "filter_type": "text_array",
                            "property_name": "prop_text_array",
                            "operator": "contains_any",
                            "value": ["one", "two"],
                        },
                        {
                            "filter_type": "boolean",
                            "property_name": "prop_bool",
                            "operator": "=",
                            "value": True,
                        },
                        {
                            "filter_type": "boolean_array",
                            "property_name": "prop_bool_array",
                            "operator": "contains_any",
                            "value": [True, False],
                        },
                        {
                            "filter_type": "date_range",
                            "property_name": "prop_date",
                            "value": {
                                "date_from": "2025-01-01T12:01:23Z",
                                "date_to": "2025-01-02T12:01:23Z",
                                "inclusive_from": True,
                                "inclusive_to": True,
                            },
                        },
                        {
                            "filter_type": "date_range",
                            "property_name": "prop_date",
                            "value": {
                                "exact_timestamp": "2025-01-01T12:01:23Z",
                                "operator": "=",
                            },
                        },
                        {
                            "filter_type": "date_array",
                            "property_name": "prop_date_array",
                            "operator": "contains_all",
                            "value": [
                                "2025-01-01T12:01:23Z",
                                "2025-01-02T12:01:23Z",
                            ],
                        },
                        {
                            "filter_type": "geo",
                            "property_name": "prop_geo",
                            "latitude": 10.0,
                            "longitude": 20.0,
                            "max_distance_meters": 30.0,
                        },
                        {
                            "filter_type": "something_new",
                            "property_name": "strange_property",
                            "value": "xyz",
                        },
                    ]
                ],
                "filter_operators": "AND",
            },
        ]
    ],
    "aggregations": [
        [
            {
                "collection": "test_collection",
                "search_query": None,
                "groupby_property": None,
                "aggregations": [
                    {
                        "aggregation_type": "integer",
                        "property_name": "prop_int",
                        "metrics": "MEAN",
                    },
                    {
                        "aggregation_type": "text",
                        "property_name": "prop_text",
                        "metrics": "COUNT",
                        "top_occurrences_limit": 10,
                    },
                    {
                        "aggregation_type": "boolean",
                        "property_name": "prop_bool",
                        "metrics": "PERCENTAGE_TRUE",
                    },
                    {
                        "aggregation_type": "date",
                        "property_name": "prop_date",
                        "metrics": "MAXIMUM",
                    },
                    {
                        "aggregation_type": "something_new",
                        "property_name": "strange_property",
                        "metrics": "XYZ",
                    },
                ],
                "filters": [],
            }
        ]
    ],
    "sources": [{"object_id": "123", "collection": "test_collection"}],
    "usage": {
        "requests": 1,
        "request_tokens": 10,
        "response_tokens": 20,
        "total_tokens": 30,
        "details": {},
    },
    "total_time": 0.1,
    "is_partial_answer": False,
    "missing_information": [],
    "final_answer": "final answer",
}


def fake_post_success(*args, **kwargs) -> FakeResponse:
    """Simulate a successful HTTP POST response.

    Returns:
        FakeResponse: A fake HTTP response with status code 200.
    """
    return FakeResponse(200, FAKE_SUCCESS_JSON)


async def fake_async_post_success(*args, **kwargs) -> FakeResponse:
    return fake_post_success(*args, **kwargs)


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


async def fake_async_post_failure(*args, **kwargs):
    return fake_post_failure(*args, **kwargs)


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

    with pytest.warns(UserWarning):
        # Expect a warning when parsing the unkown "something_new" filter/aggregation
        result = agent.run("test query")
    assert isinstance(result, QueryAgentResponse)
    assert result.original_query == "test query"
    assert result.collection_names == ["test_collection"]
    assert result.total_time == 0.1
    assert result.final_answer == "final answer"


async def test_async_run_success(monkeypatch):
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_async_post_success)
    dummy_client = DummyClient()
    agent = AsyncQueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    with pytest.warns(UserWarning):
        # Expect a warning when parsing the unkown "something_new" filter/aggregation
        result = await agent.run("test query")
    assert isinstance(result, QueryAgentResponse)
    assert result.original_query == "test query"
    assert result.collection_names == ["test_collection"]
    assert result.total_time == 0.1
    assert result.final_answer == "final answer"


class MockIterSSESuccess:
    def iter_sse(self):
        yield ServerSentEvent(
            event="progress_message",
            data=json.dumps(
                {
                    "output_type": "progress_message",
                    "stage": "query_analysis",
                    "message": "Analyzing query...",
                    "details": {},
                }
            ),
        )
        yield ServerSentEvent(
            event="streamed_tokens",
            data=json.dumps(
                {
                    "output_type": "streamed_tokens",
                    "delta": "final",
                }
            ),
        )
        yield ServerSentEvent(
            event="streamed_tokens",
            data=json.dumps({"output_type": "streamed_tokens", "delta": " answer"}),
        )
        yield ServerSentEvent(event="final_state", data=json.dumps(FAKE_SUCCESS_JSON))

    async def aiter_sse(self):
        for event in self.iter_sse():
            yield event


@contextmanager
def mock_connect_sse_success(*args, **kwargs):
    yield MockIterSSESuccess()


def test_stream_success(monkeypatch):
    monkeypatch.setattr(
        "weaviate_agents.query.query_agent.connect_sse", mock_connect_sse_success
    )
    dummy_client = DummyClient()
    agent = QueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    all_results = []
    for result in agent.stream("test query"):
        all_results.append(result)

    assert len(all_results) == 4

    assert all_results[0] == ProgressMessage(
        stage="query_analysis", message="Analyzing query..."
    )
    assert all_results[1] == StreamedTokens(delta="final")
    assert all_results[2] == StreamedTokens(delta=" answer")

    assert isinstance(all_results[3], QueryAgentResponse)
    assert all_results[3].original_query == "test query"
    assert all_results[3].collection_names == ["test_collection"]
    assert all_results[3].total_time == 0.1
    assert all_results[3].final_answer == "final answer"


@asynccontextmanager
async def mock_aconnect_sse_success(*args, **kwargs):
    yield MockIterSSESuccess()


async def test_async_stream_success(monkeypatch):
    monkeypatch.setattr(
        "weaviate_agents.query.query_agent.aconnect_sse", mock_aconnect_sse_success
    )
    dummy_client = DummyClient()
    agent = AsyncQueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    all_results = []
    async for result in agent.stream("test query"):
        all_results.append(result)

    assert len(all_results) == 4

    assert all_results[0] == ProgressMessage(
        stage="query_analysis", message="Analyzing query..."
    )
    assert all_results[1] == StreamedTokens(delta="final")
    assert all_results[2] == StreamedTokens(delta=" answer")

    assert isinstance(all_results[3], QueryAgentResponse)
    assert all_results[3].original_query == "test query"
    assert all_results[3].collection_names == ["test_collection"]
    assert all_results[3].total_time == 0.1
    assert all_results[3].final_answer == "final answer"


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


async def test_async_run_failure(monkeypatch):
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_async_post_failure)
    dummy_client = DummyClient()
    agent = AsyncQueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    with pytest.raises(Exception) as exc_info:
        await agent.run("failure query")

    assert (
        str(exc_info.value)
        == "{'error': {'message': 'Test error message', 'code': 'test_error_code', 'details': {'info': 'test detail'}}}"
    )


class MockIterSSEFailure:
    def iter_sse(self):
        yield ServerSentEvent(
            event="progress_message",
            data=json.dumps(
                {
                    "output_type": "progress_message",
                    "stage": "query_analysis",
                    "message": "Analyzing query...",
                    "details": {},
                }
            ),
        )
        yield ServerSentEvent(
            event="error",
            data=json.dumps(
                {
                    "error": {
                        "error": {
                            "message": "Test error message",
                            "code": "test_error_code",
                            "details": {"info": "test detail"},
                        }
                    }
                }
            ),
        )

    async def aiter_sse(self):
        for event in self.iter_sse():
            yield event


@contextmanager
def mock_connect_sse_failure(*args, **kwargs):
    yield MockIterSSEFailure()


def test_stream_failure(monkeypatch):
    monkeypatch.setattr(
        "weaviate_agents.query.query_agent.connect_sse", mock_connect_sse_failure
    )
    dummy_client = DummyClient()
    agent = QueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    all_results = []
    with pytest.raises(Exception) as exc_info:
        for result in agent.stream("failure query"):
            all_results.append(result)

    # Should have received the progress message before the exception
    assert len(all_results) == 1
    assert all_results[0] == ProgressMessage(
        stage="query_analysis", message="Analyzing query..."
    )
    assert (
        str(exc_info.value)
        == "{'error': {'message': 'Test error message', 'code': 'test_error_code', 'details': {'info': 'test detail'}}}"
    )


@asynccontextmanager
async def mock_aconnect_sse_failure(*args, **kwargs):
    yield MockIterSSEFailure()


async def test_async_stream_failure(monkeypatch):
    monkeypatch.setattr(
        "weaviate_agents.query.query_agent.aconnect_sse", mock_aconnect_sse_failure
    )
    dummy_client = DummyClient()
    agent = AsyncQueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    all_results = []
    with pytest.raises(Exception) as exc_info:
        async for result in agent.stream("failure query"):
            all_results.append(result)

    # Should have received the progress message before the exception
    assert len(all_results) == 1
    assert all_results[0] == ProgressMessage(
        stage="query_analysis", message="Analyzing query..."
    )
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
    with pytest.warns(UserWarning):
        # Expect a warning when parsing the unkown "something_new" filter/aggregation
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
    with pytest.warns(UserWarning):
        # Expect a warning when parsing the unkown "something_new" filter/aggregation
        result = agent.run(
            "test query",
            collections=[
                QueryAgentCollectionConfig(
                    name="test_collection",
                    target_vector=["first_vector", "second_vector"],
                )
            ],
        )
    assert isinstance(result, QueryAgentResponse)
    assert captured["json"]["collections"][0]["target_vector"] == [
        "first_vector",
        "second_vector",
    ]


async def test_async_run_with_target_vector(monkeypatch):
    captured = {}

    async def fake_async_post_with_capture(*args, **kwargs):
        captured["json"] = kwargs.get("json")
        return await fake_async_post_success()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_async_post_with_capture)
    dummy_client = DummyClient()
    agent = AsyncQueryAgent(dummy_client, agents_host="http://dummy-agent")
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    # Test with single target vector
    with pytest.warns(UserWarning):
        # Expect a warning when parsing the unkown "something_new" filter/aggregation
        result = await agent.run(
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
    with pytest.warns(UserWarning):
        # Expect a warning when parsing the unkown "something_new" filter/aggregation
        result = await agent.run(
            "test query",
            collections=[
                QueryAgentCollectionConfig(
                    name="test_collection",
                    target_vector=["first_vector", "second_vector"],
                )
            ],
        )
    assert isinstance(result, QueryAgentResponse)
    assert captured["json"]["collections"][0]["target_vector"] == [
        "first_vector",
        "second_vector",
    ]


@pytest.mark.parametrize("include_progress", [True, False])
@pytest.mark.parametrize("include_final_state", [True, False])
def test_stream_with_include_progress_and_final_state(
    monkeypatch, include_progress, include_final_state
):
    captured = {}

    @contextmanager
    def mock_connect_sse_capture(json, **kwargs):
        captured["json"] = json
        yield MockIterSSESuccess()

    monkeypatch.setattr(
        "weaviate_agents.query.query_agent.connect_sse", mock_connect_sse_capture
    )
    dummy_client = DummyClient()
    agent = QueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    # Iterate fully over the stream
    for _ in agent.stream(
        "test query",
        collections=["test_collection"],
        include_progress=include_progress,
        include_final_state=include_final_state,
    ):
        pass
    assert captured["json"]["include_progress"] == include_progress
    assert captured["json"]["include_final_state"] == include_final_state


@pytest.mark.parametrize("include_progress", [True, False])
@pytest.mark.parametrize("include_final_state", [True, False])
async def test_async_stream_with_include_progress_and_final_state(
    monkeypatch, include_progress, include_final_state
):
    captured = {}

    @asynccontextmanager
    async def mock_aconnect_sse_capture(json, **kwargs):
        captured["json"] = json
        yield MockIterSSESuccess()

    monkeypatch.setattr(
        "weaviate_agents.query.query_agent.aconnect_sse", mock_aconnect_sse_capture
    )
    dummy_client = DummyClient()
    agent = AsyncQueryAgent(
        dummy_client, ["test_collection"], agents_host="http://dummy-agent"
    )
    agent._connection = dummy_client
    agent._headers = dummy_client.additional_headers

    # Iterate fully over the stream
    async for _ in agent.stream(
        "test query",
        collections=["test_collection"],
        include_progress=include_progress,
        include_final_state=include_final_state,
    ):
        pass
    assert captured["json"]["include_progress"] == include_progress
    assert captured["json"]["include_final_state"] == include_final_state
