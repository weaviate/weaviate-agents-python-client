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

    def update_all(self) -> List[TransformationResponse]:
        """Triggers all configured transformation operations on the collection.

        Returns:
            List[TransformationResponse]: A list containing TransformationResponse objects for each
                operation, with workflow IDs and operation names for tracking transformation progress.

        Raises:
            httpx.HTTPError: If there is an error communicating with the transformation service.
            ValueError: If the operations are not properly configured or if there are duplicate
                property operations.
        """
        # Check for duplicate property operations
        property_operations = {}
        for operation in self.operations:
            property_name = operation.property_name
            if property_name in property_operations:
                raise ValueError(
                    f"Duplicate operation detected for property '{property_name}'. "
                    "Multiple operations on the same property are not allowed simultaneously."
                )
            property_operations[property_name] = operation.operation_type

        # Convert operations to request format
        request_operations = []
        for operation in self.operations:
            if operation.operation_type == OperationType.APPEND:
                if not isinstance(operation, AppendPropertyOperation):
                    raise ValueError(
                        "Append operations must use AppendPropertyOperation type"
                    )
                request_operation = {
                    "type": "create",
                    "instruction": operation.instruction,
                    "view_properties": operation.view_properties,
                    "on_properties": [
                        {
                            "name": operation.property_name,
                            "data_type": operation.data_type.value,
                        }
                    ],
                }
            elif operation.operation_type == OperationType.UPDATE:
                if not isinstance(operation, UpdatePropertyOperation):
                    raise ValueError(
                        "Update operations must use UpdatePropertyOperation type"
                    )
                request_operation = {
                    "type": "update",
                    "instruction": operation.instruction,
                    "view_properties": operation.view_properties,
                    "on_properties": [operation.property_name],
                }
            else:
                raise ValueError(
                    f"Unsupported operation type: {operation.operation_type}. "
                    "Only APPEND and UPDATE operations are supported."
                )
            request_operations.append(request_operation)

        request = {
            "collection": self.collection,
            "operations": request_operations,
        }

        # Send the requests array directly
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                self.t_host + "/properties",
                json=request,
                headers=self._headers,
            )

            if response.is_error:
                raise Exception(response.text)

            json_response = response.json()

            # Handle array response
            if isinstance(json_response, list):
                return [
                    TransformationResponse(
                        workflow_id=resp["workflow_id"],
                        operation_name=f"{self.operations[i].property_name}",
                    )
                    for i, resp in enumerate(json_response)
                ]

            # Handle single response (fallback for backward compatibility)
            return [TransformationResponse(**json_response)]

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

            if response.is_error:
                raise Exception(response.text)

            return response.json()
