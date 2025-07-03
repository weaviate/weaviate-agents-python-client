from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import (
    Any,
    AsyncGenerator,
    Coroutine,
    Generator,
    Generic,
    Literal,
    Optional,
    Union,
    overload,
)

import httpx
from httpx_sse import ServerSentEvent, aconnect_sse, connect_sse
from weaviate.client import WeaviateAsyncClient, WeaviateClient

from weaviate_agents.base import ClientType, _BaseAgent
from weaviate_agents.query.classes import (
    ProgressMessage,
    QueryAgentCollectionConfig,
    QueryAgentResponse,
    StreamedTokens,
)


class _BaseQueryAgent(Generic[ClientType], _BaseAgent[ClientType], ABC):
    """An agent for executing agentic queries against Weaviate.

    Warning:
        Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query)
    """

    def __init__(
        self,
        client: ClientType,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        agents_host: Union[str, None] = None,
        system_prompt: Union[str, None] = None,
        timeout: Union[int, None] = None,
    ):
        """Initialize the Query Agent.

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
        self.agent_url = f"{self._agents_host}/agent"

    def _prepare_request_body(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        **kwargs,
    ) -> dict:
        """Prepare the request body for the query.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            context: Optional previous response from the agent.
            **kwargs: Additional keyword arguments to pass to the request body.
        """
        collections = collections or self._collections
        if not collections:
            raise ValueError("No collections provided to the query agent.")

        return {
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
            **kwargs,
        }

    @abstractmethod
    def run(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> Union[QueryAgentResponse, Coroutine[Any, Any, QueryAgentResponse]]:
        """Run the query agent. Must be implemented by subclasses."""
        pass

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> Union[
        Generator[
            Union[ProgressMessage, StreamedTokens, QueryAgentResponse], None, None
        ],
        AsyncGenerator[
            Union[ProgressMessage, StreamedTokens, QueryAgentResponse], None
        ],
    ]:
        pass

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedTokens], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedTokens], None],
    ]:
        pass

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> Union[
        Generator[Union[StreamedTokens, QueryAgentResponse], None, None],
        AsyncGenerator[Union[StreamedTokens, QueryAgentResponse], None],
    ]:
        pass

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> Union[
        Generator[StreamedTokens, None, None],
        AsyncGenerator[StreamedTokens, None],
    ]:
        pass

    @abstractmethod
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
    ) -> Union[
        Generator[
            Union[ProgressMessage, StreamedTokens, QueryAgentResponse], None, None
        ],
        AsyncGenerator[
            Union[ProgressMessage, StreamedTokens, QueryAgentResponse], None
        ],
    ]:
        """Stream from the query agent. Must be implemented by subclasses."""
        pass


class QueryAgent(_BaseQueryAgent[WeaviateClient]):
    """An agent for executing agentic queries against Weaviate.

    Warning:
        Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query)
    """

    def run(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> QueryAgentResponse:
        """Run the query agent.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            context: Optional previous response from the agent.
        """
        request_body = self._prepare_request_body(query, collections, context)

        response = httpx.post(
            self.agent_url + "/query",
            headers=self._headers,
            json=request_body,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(response.text)

        return QueryAgentResponse(**response.json())

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> Generator[
        Union[ProgressMessage, StreamedTokens, QueryAgentResponse], None, None
    ]: ...

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> Generator[Union[ProgressMessage, StreamedTokens], None, None]: ...

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> Generator[Union[StreamedTokens, QueryAgentResponse], None, None]: ...

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> Generator[StreamedTokens, None, None]: ...

    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
    ):
        request_body = self._prepare_request_body(
            query,
            collections,
            context,
            include_progress=include_progress,
            include_final_state=include_final_state,
        )
        with httpx.Client() as client:
            with connect_sse(
                client=client,
                method="POST",
                url=self.agent_url + "/stream_query",
                json=request_body,
                headers=self._headers,
                timeout=self._timeout,
            ) as events:
                for sse in events.iter_sse():
                    output = _parse_sse(sse)
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, QueryAgentResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output


class AsyncQueryAgent(_BaseQueryAgent[WeaviateAsyncClient]):
    """An agent for executing agentic queries against Weaviate.

    Warning:
        Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query)
    """

    async def run(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> QueryAgentResponse:
        """Run the query agent.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            context: Optional previous response from the agent.
        """
        request_body = self._prepare_request_body(query, collections, context)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.agent_url + "/query",
                headers=self._headers,
                json=request_body,
                timeout=self._timeout,
            )

            if response.is_error:
                raise Exception(response.text)

            return QueryAgentResponse(**response.json())

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> AsyncGenerator[
        Union[ProgressMessage, StreamedTokens, QueryAgentResponse], None
    ]: ...

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> AsyncGenerator[Union[ProgressMessage, StreamedTokens], None]: ...

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> AsyncGenerator[Union[StreamedTokens, QueryAgentResponse], None]: ...

    @overload
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> AsyncGenerator[StreamedTokens, None]: ...

    async def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
    ):
        request_body = self._prepare_request_body(
            query,
            collections,
            context,
            include_progress=include_progress,
            include_final_state=include_final_state,
        )
        async with httpx.AsyncClient() as client:
            async with aconnect_sse(
                client=client,
                method="POST",
                url=self.agent_url + "/stream_query",
                json=request_body,
                headers=self._headers,
                timeout=self._timeout,
            ) as events:
                async for sse in events.aiter_sse():
                    output = _parse_sse(sse)
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, QueryAgentResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output


def _parse_sse(
    sse: ServerSentEvent,
) -> Union[ProgressMessage, StreamedTokens, QueryAgentResponse]:
    try:
        data = sse.json()
    except JSONDecodeError:
        raise Exception(f"Unable to decode response: {sse.event=}, {sse.data=}")

    if sse.event == "error":
        raise Exception(str(data["error"]))
    elif sse.event == "progress_message":
        return ProgressMessage.model_validate(data)
    elif sse.event == "streamed_tokens":
        return StreamedTokens.model_validate(data)
    elif sse.event == "final_state":
        return QueryAgentResponse.model_validate(data)
    else:
        raise Exception(
            f"Unrecognised event type in response: {sse.event=}, {sse.data=}"
        )
