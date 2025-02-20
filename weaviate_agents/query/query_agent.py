from typing import List, Optional, Union

import httpx
from weaviate.client import WeaviateAsyncClient, WeaviateClient

from weaviate_agents.base import _BaseAgent
from weaviate_agents.errors import QueryAgentError
from weaviate_agents.query.classes import CollectionDescription, QueryAgentResponse


class QueryAgent(_BaseAgent):
    """An agent for executing agentic queries against Weaviate.

    Warning:
        Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version.

        For more information, see the [Weaviate Agents - Query Agent](TODO: add docs link)
    """

    def __init__(
        self,
        client: Union[WeaviateClient, WeaviateAsyncClient],
        collections: List[Union[str, CollectionDescription]],
        agents_host: Union[str, None] = None,
        system_prompt: Union[str, None] = None,
        timeout: Union[int, None] = None,
    ):
        """Initialize the QueryAgent.

        Warning:
            Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
            breaking changes. Please ensure you are using the latest version.

            For more information, see the [Weaviate Agents - Query Agent](TODO: add docs link)

        Args:
            client: The Weaviate client connected to a Weaviate Cloud cluster.
            collections: The collections to query.
            agents_host: Optional host of the agents service.
            system_prompt: Optional system prompt for the agent.
            timeout: The timeout for the request. Defaults to 60 seconds.
        """
        super().__init__(client, agents_host)

        self._collections = collections
        self._system_prompt = system_prompt

        self._timeout = 60 if timeout is None else timeout

        self.q_host = f"{self._agents_host}/agent/query"

    def run(
        self,
        query: str,
        view_properties: Optional[List[str]] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> QueryAgentResponse:
        """
        Run the query agent.

        Args:
            query: The natural language query string for the agent.
            view_properties: Optional list of of property names the agent has the ability to view
                across all collections.
            context: Optional previous response from the agent.
        """
        request_body = {
            "query": query,
            "collection_names": [
                c.name if isinstance(c, CollectionDescription) else c
                for c in self._collections
            ],
            "headers": self._connection.additional_headers,
            "collection_view_properties": view_properties,
            "limit": 20,
            "tenant": None,
            "previous_response": context.model_dump() if context else None,
            "system_prompt": self._system_prompt,
        }

        response = httpx.post(
            self.q_host,
            headers=self._headers,
            json=request_body,
            timeout=self._timeout,
        )

        if response.status_code != 200:
            error_data = response.json().get("error", {})
            raise QueryAgentError(
                message=error_data.get("message", "Unknown error"),
                code=error_data.get("code", "unknown"),
                details=error_data.get("details", {}),
                status_code=response.status_code,
            )

        return QueryAgentResponse(**response.json())

    def add_collection(self, collection: Union[str, CollectionDescription]):
        """Add a collection to the query agent.

        Args:
            collection: The collection to add.
        """
        new_collection_name = (
            collection.name
            if isinstance(collection, CollectionDescription)
            else collection
        )
        for c in self._collections:
            if isinstance(c, CollectionDescription):
                if c.name == new_collection_name:
                    return
            elif c == new_collection_name:
                return
        self._collections.append(collection)

    def remove_collection(self, collection: Union[str, CollectionDescription]):
        """Remove a collection from the query agent if it exists.

        Args:
            collection: The collection to remove. Can be either a string name or CollectionDescription.
        """
        target_name = (
            collection.name
            if isinstance(collection, CollectionDescription)
            else collection
        )

        self._collections = [
            c
            for c in self._collections
            if (isinstance(c, CollectionDescription) and c.name != target_name)
            or (isinstance(c, str) and c != target_name)
        ]
