from typing import Optional, Union

import httpx
from weaviate.client import WeaviateClient

from weaviate_agents.base import _BaseAgent
from weaviate_agents.query.classes import QueryAgentCollectionConfig, QueryAgentResponse


class QueryAgent(_BaseAgent):
    """An agent for executing agentic queries against Weaviate.

    Warning:
        Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query)
    """

    def __init__(
        self,
        client: WeaviateClient,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        agents_host: Union[str, None] = None,
        system_prompt: Union[str, None] = None,
        timeout: Union[int, None] = None,
    ):
        """Initialize the QueryAgent.

        Warning:
            Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
            breaking changes. Please ensure you are using the latest version.

            For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query)

        Args:
            client: The Weaviate client connected to a Weaviate Cloud cluster.
            collections: The collections to query. Will be overriden if passed in the `run` method.
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
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> QueryAgentResponse:
        """
        Run the query agent.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            context: Optional previous response from the agent.
        """

        collections = collections or self._collections
        if not collections:
            raise ValueError("No collections provided to the query agent.")

        request_body = {
            "query": query,
            "collections": [
                collection
                if isinstance(collection, str)
                else collection.model_dump(mode="json")
                for collection in collections
            ],
            "headers": self._connection.additional_headers,
            "limit": 20,
            "previous_response": context.model_dump(mode="json") if context else None,
            "system_prompt": self._system_prompt,
        }

        response = httpx.post(
            self.q_host,
            headers=self._headers,
            json=request_body,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(response.text)

        return QueryAgentResponse(**response.json())
