from typing import Any, Dict, List, Union

import httpx
import pytest
from weaviate.collections.classes.config import DataType

from weaviate_agents.transformation.classes import (
    AppendPropertyOperation,
    OperationType,
    TransformationResponse,
    UpdatePropertyOperation,
)
from weaviate_agents.transformation.transformation_agent import TransformationAgent


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
        _json (Union[Dict[str, Any], List[Dict[str, Any]]]): The JSON data to return.
    """

    def __init__(
        self, status_code: int, json_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ):
        self.status_code = status_code
        self.is_error = 400 <= status_code <= 599
        self._json = json_data
        self.text = json_data

    def json(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Return the JSON data of the fake response.

        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: The JSON data.
        """
        return self._json


def fake_post_success(*args, **kwargs) -> FakeResponse:
    """Simulate a successful HTTP POST response.

    Returns:
        FakeResponse: A fake HTTP response with status code 202.
    """
    json_data = {
        "workflow_id": "test_workflow_id",
        "status": "running",
    }
    return FakeResponse(202, json_data)


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


def fake_get_status_success(*args, **kwargs) -> FakeResponse:
    """Simulate a successful HTTP GET response for status check.

    Returns:
        FakeResponse: A fake HTTP response with status code 200.
    """
    json_data = {
        "workflow_id": "workflow1",
        "status": {
            "batch_count": 40,
            "end_time": "2024-03-05 14:23:39",
            "start_time": "2024-03-05 14:21:15",
            "state": "completed",
            "total_duration": 144.191817,
            "total_items": 10000,
        },
    }
    return FakeResponse(200, json_data)


def test_update_all_success(monkeypatch):
    """Test that TransformationAgent.update_all returns valid responses when HTTP call is successful.

    Returns:
        None.
    """
    monkeypatch.setattr(httpx.Client, "post", fake_post_success)
    dummy_client = DummyClient()

    operations = [
        AppendPropertyOperation(
            property_name="test_prop1",
            instruction="test instruction 1",
            view_properties=["prop1", "prop2"],
            data_type=DataType.TEXT,
        ),
        UpdatePropertyOperation(
            property_name="test_prop2",
            instruction="test instruction 2",
            view_properties=["prop3", "prop4"],
        ),
    ]

    agent = TransformationAgent(
        dummy_client,
        collection="test_collection",
        operations=operations,
        agents_host="http://dummy-agent",
    )

    result = agent.update_all()
    assert isinstance(result, TransformationResponse)
    assert result.workflow_id == "test_workflow_id"


def test_update_all_failure(monkeypatch):
    """Test that TransformationAgent.update_all raises an exception when HTTP response indicates an error.

    Returns:
        None.
    """
    monkeypatch.setattr(httpx.Client, "post", fake_post_failure)
    dummy_client = DummyClient()

    operations = [
        AppendPropertyOperation(
            property_name="test_prop",
            instruction="test instruction",
            view_properties=["prop1"],
            data_type=DataType.TEXT,
        ),
    ]

    agent = TransformationAgent(
        dummy_client,
        collection="test_collection",
        operations=operations,
        agents_host="http://dummy-agent",
    )

    with pytest.raises(Exception):
        agent.update_all()


def test_get_status_success(monkeypatch):
    """Test that TransformationAgent.get_status returns valid response when HTTP call is successful.

    Returns:
        None.
    """
    monkeypatch.setattr(httpx.Client, "get", fake_get_status_success)
    dummy_client = DummyClient()

    agent = TransformationAgent(
        dummy_client,
        collection="test_collection",
        operations=[],
        agents_host="http://dummy-agent",
    )

    result = agent.get_status("workflow1")
    assert isinstance(result, dict)
    assert result["workflow_id"] == "workflow1"
    assert isinstance(result["status"], dict)
    assert result["status"]["batch_count"] == 40
    assert result["status"]["state"] == "completed"
    assert result["status"]["total_items"] == 10000
    assert isinstance(result["status"]["total_duration"], float)
    assert "start_time" in result["status"]
    assert "end_time" in result["status"]


def test_invalid_operation_type():
    """Test that TransformationAgent validates operation types correctly.

    Returns:
        None.
    """
    dummy_client = DummyClient()

    # Create an operation with mismatched type
    operation = UpdatePropertyOperation(
        property_name="test_prop",
        instruction="test instruction",
        view_properties=["prop1"],
    )
    operation.operation_type = OperationType.APPEND  # Force wrong type

    agent = TransformationAgent(
        dummy_client,
        collection="test_collection",
        operations=[operation],
        agents_host="http://dummy-agent",
    )

    with pytest.raises(ValueError) as exc_info:
        agent.update_all()

    assert "Append operations must use AppendPropertyOperation type" in str(
        exc_info.value
    )
