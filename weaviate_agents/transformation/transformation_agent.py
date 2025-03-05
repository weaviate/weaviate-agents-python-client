from typing import List, Union

import httpx
from weaviate.client import WeaviateClient

from weaviate_agents.base import _BaseAgent
from weaviate_agents.transformation.classes import (
    AppendPropertyOperation,
    OperationStep,
    OperationType,
    TransformationResponse,
    UpdatePropertyOperation,
)


class TransformationAgent(_BaseAgent):
    """An agent for running large scale transformations on data in Weaviate.

    Warning:
        Weaviate Agents - Transformation Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Transformation Agent Docs](https://weaviate.io/developers/agents/transformation)
    """

    def __init__(
        self,
        client: WeaviateClient,
        collection: str,
        operations: List[OperationStep],
        agents_host: Union[str, None] = None,
        timeout: Union[int, None] = None,
    ):
        """Initialize the TransformationAgent.

        Warning:
            Weaviate Agents - Transformation Agent is an early stage alpha product. The API is subject to
            breaking changes. Please ensure you are using the latest version of the client.

            For more information, see the [Weaviate Agents - Transformation Agent Docs](https://weaviate.io/developers/agents/transformation)

        Args:
            client: The Weaviate client connected to a Weaviate Cloud cluster.
            collection: The collection to perform transformations on.
            operations: A list of operations to execute on the collection.
            agents_host: Optional host of the agents service.
            timeout: The timeout for the request. Defaults to 60 seconds.
        """
        super().__init__(
            client=client,
            agents_host=agents_host,
        )
        self.collection = collection
        self.operations = operations

        self._timeout = 60 if timeout is None else timeout

        self.t_host = f"{self._agents_host}/transformation"

    def update_all(self) -> TransformationResponse:
        """Execute all configured transformation operations on the collection.

        This method processes operations sequentially, supporting both property creation
        (append) and update operations.

        Returns:
            TransformationResponse: Contains the workflow ID and operation name for tracking
                the transformation progress.

        Raises:
            httpx.HTTPError: If there is an error communicating with the transformation service.
            ValueError: If the operations are not properly configured.
        """
        # Convert operations to request format
        requests = []
        for operation in self.operations:
            if operation.operation_type == OperationType.APPEND:
                if not isinstance(operation, AppendPropertyOperation):
                    raise ValueError(
                        "Append operations must use AppendPropertyOperation type"
                    )
                on_properties = [
                    {
                        "name": operation.property_name,
                        "data_type": operation.data_type.value,
                    }
                ]
            elif operation.operation_type == OperationType.UPDATE:
                if not isinstance(operation, UpdatePropertyOperation):
                    raise ValueError(
                        "Update operations must use UpdatePropertyOperation type"
                    )
                on_properties = [{"name": operation.property_name}]
            else:
                raise ValueError(
                    f"Unsupported operation type: {operation.operation_type}. "
                    "Only APPEND and UPDATE operations are supported."
                )

            request = {
                "type": (
                    "create"
                    if operation.operation_type == OperationType.APPEND
                    else "update"
                ),
                "collection": self.collection,
                "instruction": operation.instruction,
                "view_properties": operation.view_properties,
                "on_properties": on_properties,
            }
            requests.append(request)

        print("Requests:")
        print(requests)

        print(self.t_host + "/properties")

        # Send the requests array directly instead of wrapping it
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                self.t_host + "/properties",
                json=requests,
                headers=self._headers,
            )
            print("Response:")
            print(response.json())
            response.raise_for_status()
            print("Response:")
            print(response.json())

            return TransformationResponse(**response.json())

    def get_status(self, workflow_id: str) -> dict:
        """Check the status of a transformation workflow.

        Args:
            workflow_id: The ID of the workflow to check, obtained from TransformationResponse

        Returns:
            dict: The status response from the transformation service

        Raises:
            httpx.HTTPError: If there is an error communicating with the transformation service
        """
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(
                f"{self.t_host}/properties/status/{workflow_id}",
                headers=self._headers,
            )
            response.raise_for_status()

            return response.json()
