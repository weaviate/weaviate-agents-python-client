import warnings
from abc import ABC, abstractmethod
from json import JSONDecodeError, loads
from typing import (
    Any,
    AsyncGenerator,
    Coroutine,
    Generator,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    overload,
)

import httpx
from httpx_sse import ServerSentEvent, aconnect_sse, connect_sse
from pydantic import BaseModel
from typing_extensions import deprecated
from weaviate.client import WeaviateAsyncClient, WeaviateClient

from weaviate_agents.base import ClientType, _BaseAgent
from weaviate_agents.query.classes import (
    AskModeResponse,
    ParsedAskModeResponse,
    ProgressMessage,
    QueryAgentCollectionConfig,
    QueryAgentResponse,
    ResearchModeResponse,
    StreamedThoughts,
    StreamedTokens,
    SuggestQueryResponse,
)
from weaviate_agents.query.classes.request import ChatMessage, ConversationContext
from weaviate_agents.query.search import (
    AsyncQueryAgentSearcher,
    AsyncSearchModeResponse,
    QueryAgentSearcher,
    SearchModeResponse,
)

# Bound to BaseModel so a `output_format=MyModel` call flows the concrete model
# type through to `ParsedAskModeResponse[MyModel].final_answer_parsed`.
M = TypeVar("M", bound=BaseModel)


class _BaseQueryAgent(Generic[ClientType], _BaseAgent[ClientType], ABC):
    def __init__(
        self,
        client: ClientType,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        agents_host: Union[str, None] = None,
        system_prompt: Union[str, None] = None,
        timeout: Union[int, None] = None,
    ):
        super().__init__(client, agents_host)

        self._collections = collections
        self._system_prompt = system_prompt

        self._timeout = 60 if timeout is None else timeout
        self.agent_url = f"{self._agents_host}/agent"
        self.query_url = f"{self._agents_host}/query"

    def _prepare_request_body(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        output_format: Union[None, dict[str, Any], type[BaseModel]] = None,
        **kwargs,
    ) -> dict:
        """Prepare the request body for the query.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            context: Optional previous response from the agent.
            output_format: The format of the output to return. Either `None` (default, no structured output), a `BaseModel` subclass, or a `dict` (a Draft 2020-12 JSON Schema).
            **kwargs: Additional keyword arguments to pass to the request body.
        """
        collections = collections or self._collections
        if not collections:
            raise ValueError("No collections provided to the query agent.")

        query_request = (
            query
            if isinstance(query, str)
            else ConversationContext(messages=query).model_dump(mode="json")
        )

        if isinstance(output_format, type) and issubclass(output_format, BaseModel):
            output_format_json = output_format.model_json_schema()
        elif isinstance(output_format, dict):
            output_format_json = output_format
        else:
            output_format_json = None

        output = {
            "query": query_request,
            "collections": [
                (
                    collection
                    if isinstance(collection, str)
                    else collection.model_dump(mode="json")
                )
                for collection in collections
            ],
            "headers": self._connection.additional_headers,
            "system_prompt": self._system_prompt,
            "output_format": output_format_json,
            **kwargs,
        }
        if context is not None:
            output["previous_response"] = context.model_dump(mode="json")
        return output

    def _prepare_research_mode_request_body(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: bool = True,
        include_thoughts: bool = True,
        include_final_state: bool = True,
    ) -> dict:
        """Prepare the request body for the research-mode query.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            reasoning_prompt: Optional prompt to control the agent's behavior during the research phase.
            include_progress: Whether to include progress messages in the stream.
            include_thoughts: Whether to include streamed thoughts in the stream.
            include_final_state: Whether to include the final state in the stream.
        """
        collections = collections or self._collections
        if not collections:
            raise ValueError("No collections provided to the query agent.")

        query_request = (
            query
            if isinstance(query, str)
            else ConversationContext(messages=query).model_dump(mode="json")
        )
        output = {
            "query": query_request,
            "collections": [
                (
                    collection
                    if isinstance(collection, str)
                    else collection.model_dump(mode="json")
                )
                for collection in collections
            ],
            "headers": self._connection.additional_headers,
            "agent_system_prompt": reasoning_prompt,
            "final_answer_system_prompt": self._system_prompt,
            "include_progress": include_progress,
            "include_thoughts": include_thoughts,
            "include_final_state": include_final_state,
        }

        return output

    @deprecated(
        "QueryAgent.run() is deprecated and will be removed in a future release. "
        "Use QueryAgent.ask() instead."
    )
    @abstractmethod
    def run(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> Union[QueryAgentResponse, Coroutine[Any, Any, QueryAgentResponse]]:
        """*Deprecated: the `run` method is deprecated; use `ask` instead*.

        Run the query agent.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            context: Optional previous response from the agent.
        """
        pass

    @overload
    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Union[
        ParsedAskModeResponse[M], Coroutine[Any, Any, ParsedAskModeResponse[M]]
    ]: ...

    @overload
    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Union[
        ParsedAskModeResponse[dict], Coroutine[Any, Any, ParsedAskModeResponse[dict]]
    ]: ...

    @overload
    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Union[AskModeResponse, Coroutine[Any, Any, AskModeResponse]]: ...

    @abstractmethod
    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: Union[dict[str, Any], type[BaseModel], None] = None,
    ) -> Union[
        AskModeResponse,
        ParsedAskModeResponse[Any],
        Coroutine[Any, Any, Union[AskModeResponse, ParsedAskModeResponse[Any]]],
    ]:
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

    @deprecated(
        "QueryAgent.stream() is deprecated and will be removed in a future release. "
        "Use QueryAgent.ask_stream() instead."
    )
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
        """*Deprecated: the `stream` method is deprecated; use `ask_stream` instead*.

        Stream from the query agent.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            context: Optional previous response from the agent.
            include_progress: Whether to include progress messages in the stream. These are informational messages about the progress of the agent's search.
            include_final_state: Whether to include the final state in the stream. This is the final response class, ``QueryAgentResponse``, that will be the last item in the stream.
        """
        pass

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Union[
        Generator[
            Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[M]], None, None
        ],
        AsyncGenerator[
            Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[M]], None
        ],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Union[
        Generator[
            Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[dict]],
            None,
            None,
        ],
        AsyncGenerator[
            Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[dict]], None
        ],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedTokens, AskModeResponse], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedTokens, AskModeResponse], None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedTokens], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedTokens], None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedTokens], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedTokens], None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedTokens], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedTokens], None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Union[
        Generator[Union[StreamedTokens, ParsedAskModeResponse[M]], None, None],
        AsyncGenerator[Union[StreamedTokens, ParsedAskModeResponse[M]], None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Union[
        Generator[Union[StreamedTokens, ParsedAskModeResponse[dict]], None, None],
        AsyncGenerator[Union[StreamedTokens, ParsedAskModeResponse[dict]], None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Union[
        Generator[Union[StreamedTokens, AskModeResponse], None, None],
        AsyncGenerator[Union[StreamedTokens, AskModeResponse], None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Union[
        Generator[StreamedTokens, None, None],
        AsyncGenerator[StreamedTokens, None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Union[
        Generator[StreamedTokens, None, None],
        AsyncGenerator[StreamedTokens, None],
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Union[
        Generator[StreamedTokens, None, None],
        AsyncGenerator[StreamedTokens, None],
    ]: ...

    @abstractmethod
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: Union[dict[str, Any], type[BaseModel], None] = None,
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedTokens, AskModeResponse], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedTokens, AskModeResponse], None],
    ]:
        pass

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> Union[
        Generator[
            Union[
                ProgressMessage, StreamedThoughts, StreamedTokens, ResearchModeResponse
            ],
            None,
            None,
        ],
        AsyncGenerator[
            Union[
                ProgressMessage, StreamedThoughts, StreamedTokens, ResearchModeResponse
            ],
            None,
        ],
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedThoughts, StreamedTokens], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedThoughts, StreamedTokens], None],
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> Union[
        Generator[
            Union[ProgressMessage, StreamedTokens, ResearchModeResponse], None, None
        ],
        AsyncGenerator[
            Union[ProgressMessage, StreamedTokens, ResearchModeResponse], None
        ],
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> Union[
        Generator[Union[ProgressMessage, StreamedTokens], None, None],
        AsyncGenerator[Union[ProgressMessage, StreamedTokens], None],
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> Union[
        Generator[
            Union[StreamedThoughts, StreamedTokens, ResearchModeResponse], None, None
        ],
        AsyncGenerator[
            Union[StreamedThoughts, StreamedTokens, ResearchModeResponse], None
        ],
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> Union[
        Generator[Union[StreamedThoughts, StreamedTokens], None, None],
        AsyncGenerator[Union[StreamedThoughts, StreamedTokens], None],
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> Union[
        Generator[Union[StreamedTokens, ResearchModeResponse], None, None],
        AsyncGenerator[Union[StreamedTokens, ResearchModeResponse], None],
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> Union[
        Generator[StreamedTokens, None, None],
        AsyncGenerator[StreamedTokens, None],
    ]: ...

    @abstractmethod
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: bool = True,
        include_thoughts: bool = True,
        include_final_state: bool = True,
    ) -> Union[
        Generator[
            Union[
                ProgressMessage, StreamedThoughts, StreamedTokens, ResearchModeResponse
            ],
            None,
            None,
        ],
        AsyncGenerator[
            Union[
                ProgressMessage, StreamedThoughts, StreamedTokens, ResearchModeResponse
            ],
            None,
        ],
    ]:
        pass

    @abstractmethod
    def search(
        self,
        query: Union[str, list[ChatMessage]],
        limit: int = 20,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        filtering: Optional[Literal["recall", "precision"]] = None,
        diversity_weight: Optional[float] = None,
    ) -> Union[SearchModeResponse, Coroutine[Any, Any, AsyncSearchModeResponse]]:
        pass

    @abstractmethod
    def suggest_queries(
        self,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        num_queries: int = 3,
        instructions: Optional[str] = None,
    ) -> Union[SuggestQueryResponse, Coroutine[Any, Any, SuggestQueryResponse]]:
        pass


class QueryAgent(_BaseQueryAgent[WeaviateClient]):
    """An agent for executing agentic queries against Weaviate.

    For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents)
    """

    def __init__(
        self,
        client: WeaviateClient,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        agents_host: Union[str, None] = None,
        system_prompt: Union[str, None] = None,
        timeout: Union[int, None] = None,
    ):
        """Initialize the synchronous Query Agent.

        Args:
            client: The *synchronous* Weaviate client connected to a Weaviate Cloud cluster (i.e.
                from ``weaviate.connect_to_weaviate_cloud``).
            collections: The collections to query. Either a list of strings, or a
                list of :class:`~weaviate_agents.query.classes.QueryAgentCollectionConfig` objects.
                Will be overridden if passed in any of the agent's methods that support it.
            agents_host: Optional host of the agents service.
            system_prompt: Optional prompt to control the tone, format, and style of the agent's
                final response. This prompt is both passed to the query writer agent, and
                applied when generating the answer after all research and data retrieval is complete.
            timeout: The timeout for the request. Defaults to 60 seconds.
        """
        super().__init__(
            client=client,
            collections=collections,
            agents_host=agents_host,
            system_prompt=system_prompt,
            timeout=timeout,
        )

    @deprecated(
        "QueryAgent.run() is deprecated and will be removed in a future release. Use QueryAgent.ask() instead."
    )
    def run(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> QueryAgentResponse:
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            context=context,
            result_evaluation="none",
        )

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
    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> ParsedAskModeResponse[M]: ...

    @overload
    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> ParsedAskModeResponse[dict]: ...

    @overload
    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> AskModeResponse: ...

    def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: Union[dict[str, Any], type[BaseModel], None] = None,
    ) -> Union[AskModeResponse, ParsedAskModeResponse[Any]]:
        """Run the Query Agent ask mode.

        Perform an agentic search on the collections and return a natural language answer to the query.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Either a list of strings, or a list of :class:`~weaviate_agents.query.classes.QueryAgentCollectionConfig` objects.
                Will override any collections if passed in the constructor.
            result_evaluation: One of ``"llm"`` or ``"none"``.
                If ``"llm"``, the final answer will be cross-compared to the sources, and those sources will be filtered to only those in the answer.
                Also populates the fields `missing_information` and `is_partial_answer` of the response.
                If ``"none"``, the result will not be evaluated, and the sources will not be filtered.
                Defaults to ``"none"``.
            output_format: The structured output format to return. Either `None` (default, no structured output), a `BaseModel` subclass, or a dictionary.
                This enforces the output format of the final answer to be of this schema.
                The LLM will conform to the output format specified.
                The `final_answer` output field in the response will also be of the type specified.
                When passing a `dict`, the dictionary must conform to the Draft 2020-12 JSON Schema specification.
                Defaults to `str`.

        Returns:
            An instance of :class:`~weaviate_agents.query.classes.response.AskModeResponse` which contains the final answer, sources,
            and other metadata such as the searches performed, usage and total time.

        Examples:
            >>> from weaviate_agents import QueryAgent
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> agent.ask("What are the terms of the contract signed by John Smith in May 2025?")

            >>> from weaviate_agents import QueryAgent
            >>> from pydantic import BaseModel, Field
            >>>
            >>> class CitedText(BaseModel):
            ...     text: str
            ...     sources: list[str] = Field(description="The sources that support this section of text. Can be empty.")
            >>>
            >>> class AnswerWithSources(BaseModel):
            ...     texts: list[CitedText]
            >>>
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> result = agent.ask("What contracts were signed by Jane Doe in 2024? What were they about?", output_format=AnswerWithSources)
            >>> print(type(result.final_answer))
            <class 'AnswerWithSources'>
        """
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            result_evaluation=result_evaluation,
            output_format=output_format,
        )

        response = httpx.post(
            self.query_url + "/ask",
            headers=self._headers,
            json=request_body,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(response.text)

        return _parse_ask_result(response=response.json(), output_format=output_format)

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

    @deprecated(
        "QueryAgent.stream() is deprecated and will be removed in a future release. Use QueryAgent.ask_stream() instead."
    )
    def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
    ):
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            context=context,
            include_progress=include_progress,
            include_final_state=include_final_state,
            result_evaluation="none",
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
                if events.response.is_error:
                    events.response.read()
                    raise Exception(events.response.text)

                for sse in events.iter_sse():
                    output = _parse_sse(sse, mode="query")
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, QueryAgentResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Generator[
        Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[M]], None, None
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Generator[
        Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[dict]], None, None
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Generator[
        Union[ProgressMessage, StreamedTokens, AskModeResponse], None, None
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Generator[Union[ProgressMessage, StreamedTokens], None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Generator[Union[ProgressMessage, StreamedTokens], None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Generator[Union[ProgressMessage, StreamedTokens], None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Generator[Union[StreamedTokens, ParsedAskModeResponse[M]], None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Generator[Union[StreamedTokens, ParsedAskModeResponse[dict]], None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Generator[Union[StreamedTokens, AskModeResponse], None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> Generator[StreamedTokens, None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> Generator[StreamedTokens, None, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> Generator[StreamedTokens, None, None]: ...

    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: Union[dict[str, Any], type[BaseModel], None] = None,
    ):
        """Run the Query Agent ask mode and stream the response.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Either a list of strings, or a list of :class:`~weaviate_agents.query.classes.QueryAgentCollectionConfig` objects.
                Will override any collections if passed in the constructor.
            include_progress: Whether to include progress messages in the stream. These are informational messages about the progress of the agent's search.
            include_final_state: Whether to include the final state in the stream. This is the final response class that will be the last item in the stream.
            result_evaluation: One of ``"llm"`` or ``"none"``.
                If ``"llm"``, the final answer will be cross-compared to the sources, and those sources will be filtered to only those in the answer.
                Also populates the fields `missing_information` and `is_partial_answer` of the response.
                If ``"none"``, the result will not be evaluated, and the sources will not be filtered.
                Defaults to ``"none"``.
            output_format: The structured output format to return. Either `None` (default, no structured output), a `BaseModel` subclass, or a dictionary.
                This enforces the output format of the final answer to be of this schema.
                The LLM will conform to the output format specified.
                The `final_answer` output field in the response will also be of the type specified.
                When passing a `dict`, the dictionary must conform to the Draft 2020-12 JSON Schema specification.
                Whilst streaming, the :class:`~weaviate_agents.query.classes.response.StreamedTokens` will return delta text
                tokens on the final answer as it is being constructed as raw string tokens, not a JSON object.
                When the final answer is complete, the :class:`~weaviate_agents.query.classes.response.AskModeResponse` will be parsed
                and the `final_answer` field will be of the type specified.
                Defaults to `str`.

        Returns:
            A generator of the response stream.
            The generator will yield the following types:

            - [:class:`~weaviate_agents.query.classes.response.ProgressMessage`]: Informational messages about the progress of the agent's search (if ``include_progress`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.AskModeResponse`]: The final response class that will be the last item in the stream (if ``include_final_state`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.StreamedTokens`]: Token deltas from the agent's response.

        Examples:
            >>> from weaviate_agents import QueryAgent
            >>> from weaviate_agents.classes import AskModeResponse, StreamedTokens, ProgressMessage
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> for result in agent.ask_stream("What are the terms of the contract signed by John Smith in May 2025?"):
            ...     if isinstance(result, AskModeResponse):
            ...         result.display()
            ...     elif isinstance(result, StreamedTokens):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, ProgressMessage):
            ...         print(result.message)

            >>> from weaviate_agents import QueryAgent
            >>> from pydantic import BaseModel, Field
            >>>
            >>> class CitedText(BaseModel):
            ...     text: str
            ...     sources: list[str] = Field(description="The sources that support this section of text. Can be empty.")
            >>>
            >>> class AnswerWithSources(BaseModel):
            ...     texts: list[CitedText]
            >>>
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> for result in agent.ask_stream(
            ...     "What contracts were signed by Jane Doe in 2024? What were they about?",
            ...     output_format=AnswerWithSources
            ... ):
            ...     if isinstance(result, AskModeResponse):
            ...         result.display()
            ...     elif isinstance(result, StreamedTokens):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, ProgressMessage):
            ...         print(result.message)
        """
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            include_progress=include_progress,
            include_final_state=include_final_state,
            result_evaluation=result_evaluation,
            output_format=output_format,
        )
        with httpx.Client() as client:
            with connect_sse(
                client=client,
                method="POST",
                url=self.query_url + "/stream_ask",
                json=request_body,
                headers=self._headers,
                timeout=self._timeout,
            ) as events:
                if events.response.is_error:
                    events.response.read()
                    raise Exception(events.response.text)

                for sse in events.iter_sse():
                    output = _parse_sse(sse, mode="ask", output_format=output_format)
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, AskModeResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> Generator[
        Union[ProgressMessage, StreamedThoughts, StreamedTokens, ResearchModeResponse],
        None,
        None,
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> Generator[
        Union[ProgressMessage, StreamedThoughts, StreamedTokens], None, None
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> Generator[
        Union[ProgressMessage, StreamedTokens, ResearchModeResponse], None, None
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> Generator[Union[ProgressMessage, StreamedTokens], None, None]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> Generator[
        Union[StreamedThoughts, StreamedTokens, ResearchModeResponse], None, None
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> Generator[Union[StreamedThoughts, StreamedTokens], None, None]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> Generator[Union[StreamedTokens, ResearchModeResponse], None, None]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> Generator[StreamedTokens, None, None]: ...

    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: bool = True,
        include_thoughts: bool = True,
        include_final_state: bool = True,
    ):
        """Run the Query Agent research mode and stream the response.

        Args:
            query: The natural language query string or list of chat messages.
            collections: The collections to query. Overrides any collections
                provided in the constructor when set.
            reasoning_prompt: Optional prompt to control the agent's behavior during the
                research phase, guiding how it searches, retrieves, and reasons about data.
                The constructor's system_prompt controls the final response formatting.
            include_progress: Whether to include progress messages in the stream. These are informational messages about the progress of the agent's search.
            include_thoughts: Whether to include streamed thoughts in the stream. These are token deltas of the agent's reasoning process as it performs the research.
            include_final_state: Whether to include the final state in the stream. This is the final response class, ``ResearchModeResponse``, that will be the last item in the stream.

        Returns:
            A generator of the response stream.
            The generator will yield the following types:

            - [:class:`~weaviate_agents.query.classes.response.ProgressMessage`]: Informational messages about the progress of the agent's search (if ``include_progress`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.StreamedThoughts`]: Token deltas of the agent's reasoning process as it performs the research (if ``include_thoughts`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.ResearchModeResponse`]: The final response class that will be the last item in the stream (if ``include_final_state`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.StreamedTokens`]: Token deltas from the agent's response.

        Examples:
            >>> from weaviate_agents import QueryAgent
            >>> from weaviate_agents.classes import StreamedThoughts, StreamedTokens, ProgressMessage, ResearchModeResponse
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> for result in agent.research_stream("What are the terms of the contract signed by John Smith in May 2025?"):
            ...     if isinstance(result, ResearchModeResponse):
            ...         result.display()
            ...     elif isinstance(result, StreamedThoughts):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, StreamedTokens):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, ProgressMessage):
            ...         print(result.message)
        """
        request_body = self._prepare_research_mode_request_body(
            query=query,
            collections=collections,
            reasoning_prompt=reasoning_prompt,
            include_progress=include_progress,
            include_thoughts=include_thoughts,
            include_final_state=include_final_state,
        )
        with httpx.Client() as client:
            with connect_sse(
                client=client,
                method="POST",
                url=self.query_url + "/stream_research",
                json=request_body,
                headers=self._headers,
                timeout=self._timeout,
            ) as events:
                if events.response.is_error:
                    events.response.read()
                    raise Exception(events.response.text)

                for sse in events.iter_sse():
                    output = _parse_sse(sse, mode="research")
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, StreamedThoughts):
                        if include_thoughts:
                            yield output
                    elif isinstance(output, ResearchModeResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output

    def search(
        self,
        query: Union[str, list[ChatMessage]],
        limit: int = 20,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        filtering: Optional[Literal["recall", "precision"]] = None,
        diversity_weight: Optional[float] = None,
    ) -> SearchModeResponse:
        """Run the Query Agent search-only mode.

        This method sends the initial search request and returns a
        :class:`~weaviate_agents.query.classes.response.SearchModeResponse` containing the first page of results. To paginate,
        use the ``SearchModeResponse.next()`` method. This reuses the same
        underlying searches to ensure a consistent result set across pages.

        Args:
            query: The natural language query string for the agent.
            limit: The maximum number of results to return for the first page.
            collections: The collections to query. Either a list of strings, or a list of :class:`~weaviate_agents.query.classes.QueryAgentCollectionConfig` objects.
                Overrides any collections provided in the constructor when set.
            filtering: The filtering strategy to use for this search.
                Use "recall" to optimize for finding all relevant results,
                or "precision" to optimize for the accuracy of returned results.
                Defaults to "recall".
            diversity_weight: Optional float between 0.0 and 1.0 to diversify
                results with MMR reranking.
                Higher values push for more topical variety at the cost of relevance.
                Defaults to None (no diversity).

        Returns:
            An instance of :class:`~weaviate_agents.query.classes.response.SearchModeResponse` for the first page of results. Use
            the ``response.next(limit=..., offset=...)`` method to paginate.

        Examples:
            >>> from weaviate_agents import QueryAgent
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> agent.search("Find all NDAs signed by Jane Doe in 2024.")

            >>> from weaviate_agents import QueryAgent
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> # With pagination
            >>> page_1 = agent.search("Find all NDAs signed by Jane Doe in 2024.", limit = 5)
            >>> page_2 = page_1.next(limit = 5, offset = 5)
            >>> page_3 = page_2.next(limit = 5, offset = 10)
        """
        collections = collections or self._collections
        if not collections:
            raise ValueError("No collections provided to the query agent.")
        searcher = QueryAgentSearcher(
            headers=self._headers,
            connection_headers=self._connection.additional_headers,
            timeout=self._timeout,
            query_url=self.query_url,
            query=query,
            collections=collections,
            system_prompt=self._system_prompt,
            filtering=filtering,
            diversity_weight=diversity_weight,
        )
        return searcher.run(limit=limit)

    def suggest_queries(
        self,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        num_queries: int = 3,
        instructions: Optional[str] = None,
    ) -> SuggestQueryResponse:
        """Suggest queries for the data in your collections.

        Uses the agent to generate example queries that can be run against the given collections.

        This can help users discover what kinds of questions they can ask or generate example prompts for a dataset.

        Args:
            collections:
                Optional override for the collections configured at instantiation.
                Can be a list of collection names (str) or QueryAgentCollectionConfig objects.
            num_queries:
                The number of queries to suggest (default: 3).
            instructions:
                Optional natural language guidance for the style, topic, or language of the suggested queries.
                This is supplied in addition to the agent's system instructions.

        Returns:
            An instance of :class:`~weaviate_agents.query.classes.response.SuggestQueryResponse` which
            contains a list of suggested queries, with additional metadata if present.

        Examples:
            >>> from weaviate_agents import QueryAgent
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> agent.suggest_queries(
            ...     collections=["Products"],
            ...     num_queries=5,
            ...     instructions="Focus on questions about eco-friendly features.",
            ... )

            >>> from weaviate_agents import QueryAgent
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> agent.suggest_queries(
            ...     collections=["FinancialContracts"],
            ...     num_queries=1,
            ...     instructions="Write your question in Spanish.",
            ... )
        """
        resolved_collections = collections or self._collections
        if not resolved_collections:
            raise ValueError("No collections provided to the query agent.")

        request_body: dict[str, Any] = {
            "collections": [
                (
                    collection
                    if isinstance(collection, str)
                    else collection.model_dump(mode="json")
                )
                for collection in resolved_collections
            ],
            "num_queries": num_queries,
            "headers": self._connection.additional_headers,
        }
        if instructions is not None:
            request_body["instructions"] = instructions

        response = httpx.post(
            self.query_url + "/suggest_queries",
            headers=self._headers,
            json=request_body,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(response.text)

        return SuggestQueryResponse(**response.json())


class AsyncQueryAgent(_BaseQueryAgent[WeaviateAsyncClient]):
    """An agent for executing agentic queries against Weaviate.

    For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents)
    """

    def __init__(
        self,
        client: WeaviateAsyncClient,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        agents_host: Union[str, None] = None,
        system_prompt: Union[str, None] = None,
        timeout: Union[int, None] = None,
    ):
        """Initialize the asynchronous Query Agent.

        Args:
            client: The *asynchronous* Weaviate client connected to a Weaviate Cloud cluster (i.e.
                from ``weaviate.use_async_with_weaviate_cloud``).
            collections: The collections to query. Either a list of strings, or a list of :class:`~weaviate_agents.query.classes.QueryAgentCollectionConfig` objects.
                Will be overridden if passed in any of the agent's methods that support it.
            agents_host: Optional host of the agents service.
            system_prompt: Optional prompt to control the tone, format, and style of the agent's
                final response. This prompt is both passed to the query writer agent, and
                applied when generating the answer after all research and data retrieval is complete.
            timeout: The timeout for the request. Defaults to 60 seconds.
        """
        super().__init__(
            client=client,
            collections=collections,
            agents_host=agents_host,
            system_prompt=system_prompt,
            timeout=timeout,
        )

    @deprecated(
        "AsyncQueryAgent.run() is deprecated and will be removed in a future release. "
        "Use AsyncQueryAgent.ask() instead."
    )
    async def run(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
    ) -> QueryAgentResponse:
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            context=context,
            result_evaluation="none",
        )

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
    async def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> ParsedAskModeResponse[M]: ...

    @overload
    async def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> ParsedAskModeResponse[dict]: ...

    @overload
    async def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> AskModeResponse: ...

    async def ask(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: Union[dict[str, Any], type[BaseModel], None] = None,
    ) -> Union[AskModeResponse, ParsedAskModeResponse[Any]]:
        """Run the Query Agent ask mode.

        Perform an agentic search on the collections and return a natural language answer to the query.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Will override any collections if passed in the constructor.
            result_evaluation: One of ``"llm"`` or ``"none"``.
                If ``"llm"``, the final answer will be cross-compared to the sources, and those sources will be filtered to only those in the answer.
                Also populates the fields `missing_information` and `is_partial_answer` of the response.
                If ``"none"``, the result will not be evaluated, and the sources will not be filtered.
                Defaults to ``"none"``.
            output_format: The structured output format to return. Either `None` (default, no structured output), a `BaseModel` subclass, or a dictionary.
                This enforces the output format of the final answer to be of this schema.
                The LLM will conform to the output format specified.
                The `final_answer` output field in the response will also be of the type specified.
                When passing a `dict`, the dictionary must conform to the Draft 2020-12 JSON Schema specification.
                Defaults to `str`.

        Returns:
            An instance of :class:`~weaviate_agents.query.classes.response.AskModeResponse` which contains the final answer, sources,
            and other metadata such as the searches performed, usage and total time.

        Examples:
            >>> from weaviate_agents import AsyncQueryAgent
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> await agent.ask("What are the terms of the contract signed by John Smith in May 2025?")

            >>> from weaviate_agents import AsyncQueryAgent
            >>> from pydantic import BaseModel, Field
            >>>
            >>> class CitedText(BaseModel):
            ...     text: str
            ...     sources: list[str] = Field(description="The sources that support this section of text. Can be empty.")
            >>>
            >>> class AnswerWithSources(BaseModel):
            ...     texts: list[CitedText]
            >>>
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> result = await agent.ask("What contracts were signed by Jane Doe in 2024? What were they about?", output_format=AnswerWithSources)
            >>> print(type(result.final_answer))
            <class 'AnswerWithSources'>
        """
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            result_evaluation=result_evaluation,
            output_format=output_format,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.query_url + "/ask",
                headers=self._headers,
                json=request_body,
                timeout=self._timeout,
            )

            if response.is_error:
                raise Exception(response.text)

            return _parse_ask_result(
                response=response.json(), output_format=output_format
            )

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

    @deprecated(
        "AsyncQueryAgent.stream() is deprecated and will be removed in a future release. "
        "Use AsyncQueryAgent.ask_stream() instead."
    )
    async def stream(
        self,
        query: str,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        context: Optional[QueryAgentResponse] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
    ):
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            context=context,
            include_progress=include_progress,
            include_final_state=include_final_state,
            result_evaluation="none",
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
                if events.response.is_error:
                    await events.response.aread()
                    raise Exception(events.response.text)

                async for sse in events.aiter_sse():
                    output = _parse_sse(sse, mode="query")
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, QueryAgentResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> AsyncGenerator[
        Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[M]], None
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> AsyncGenerator[
        Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[dict]], None
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> AsyncGenerator[
        Union[ProgressMessage, StreamedTokens, AskModeResponse], None
    ]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> AsyncGenerator[Union[ProgressMessage, StreamedTokens], None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> AsyncGenerator[Union[ProgressMessage, StreamedTokens], None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[True] = True,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> AsyncGenerator[Union[ProgressMessage, StreamedTokens], None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> AsyncGenerator[Union[StreamedTokens, ParsedAskModeResponse[M]], None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> AsyncGenerator[Union[StreamedTokens, ParsedAskModeResponse[dict]], None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[True] = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> AsyncGenerator[Union[StreamedTokens, AskModeResponse], None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: type[M],
    ) -> AsyncGenerator[StreamedTokens, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        *,
        output_format: dict[str, Any],
    ) -> AsyncGenerator[StreamedTokens, None]: ...

    @overload
    def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: Literal[False] = False,
        include_final_state: Literal[False] = False,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: None = None,
    ) -> AsyncGenerator[StreamedTokens, None]: ...

    async def ask_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        include_progress: bool = True,
        include_final_state: bool = True,
        result_evaluation: Literal["llm", "none"] = "none",
        output_format: Union[dict[str, Any], type[BaseModel], None] = None,
    ):
        """Run the Query Agent ask mode and stream the response.

        Args:
            query: The natural language query string for the agent.
            collections: The collections to query. Either a list of strings, or a list of :class:`~weaviate_agents.query.classes.QueryAgentCollectionConfig` objects.
                Will override any collections if passed in the constructor.
            include_progress: Whether to include progress messages in the stream. These are informational messages about the progress of the agent's search.
            include_final_state: Whether to include the final state in the stream. This is the final response class that will be the last item in the stream.
            result_evaluation: One of ``"llm"`` or ``"none"``.
                If ``"llm"``, the final answer will be cross-compared to the sources, and those sources will be filtered to only those in the answer.
                Also populates the fields `missing_information` and `is_partial_answer` of the response.
                If ``"none"``, the result will not be evaluated, and the sources will not be filtered.
                Defaults to ``"none"``.
            output_format: The structured output format to return. Either `None` (default, no structured output), a `BaseModel` subclass, or a dictionary.
                This enforces the output format of the final answer to be of this schema.
                The LLM will conform to the output format specified.
                The `final_answer` output field in the response will also be of the type specified.
                When passing a `dict`, the dictionary must conform to the Draft 2020-12 JSON Schema specification.
                Whilst streaming, the :class:`~weaviate_agents.query.classes.response.StreamedTokens` will return delta text
                tokens on the final answer as it is being constructed as raw string tokens, not a JSON object.
                When the final answer is complete, the :class:`~weaviate_agents.query.classes.response.AskModeResponse` will be parsed
                and the `final_answer` field will be of the type specified.
                Defaults to `str`.

        Returns:
            A generator of the response stream.
            The generator will yield the following types:

            - [:class:`~weaviate_agents.query.classes.response.ProgressMessage`]: Informational messages about the progress of the agent's search (if ``include_progress`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.AskModeResponse`]: The final response class that will be the last item in the stream (if ``include_final_state`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.StreamedTokens`]: Token deltas from the agent's response.

        Examples:
            >>> from weaviate_agents import AsyncQueryAgent
            >>> from weaviate_agents.classes import AskModeResponse, StreamedTokens, ProgressMessage
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> async for result in agent.ask_stream("What are the terms of the contract signed by John Smith in May 2025?"):
            ...     if isinstance(result, AskModeResponse):
            ...         result.display()
            ...     elif isinstance(result, StreamedTokens):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, ProgressMessage):
            ...         print(result.message)

            >>> from weaviate_agents import QueryAgent
            >>> from pydantic import BaseModel, Field
            >>>
            >>> class CitedText(BaseModel):
            ...     text: str
            ...     sources: list[str] = Field(description="The sources that support this section of text. Can be empty.")
            >>>
            >>> class AnswerWithSources(BaseModel):
            ...     texts: list[CitedText]
            >>>
            >>> agent = QueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> async for result in agent.ask_stream(
            ...     "What contracts were signed by Jane Doe in 2024? What were they about?",
            ...     output_format=AnswerWithSources
            ... ):
            ...     if isinstance(result, AskModeResponse):
            ...         result.display()
            ...     elif isinstance(result, StreamedTokens):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, ProgressMessage):
            ...         print(result.message)
        """
        request_body = self._prepare_request_body(
            query=query,
            collections=collections,
            include_progress=include_progress,
            include_final_state=include_final_state,
            result_evaluation=result_evaluation,
            output_format=output_format,
        )
        async with httpx.AsyncClient() as client:
            async with aconnect_sse(
                client=client,
                method="POST",
                url=self.query_url + "/stream_ask",
                json=request_body,
                headers=self._headers,
                timeout=self._timeout,
            ) as events:
                if events.response.is_error:
                    await events.response.aread()
                    raise Exception(events.response.text)

                async for sse in events.aiter_sse():
                    output = _parse_sse(sse, mode="ask", output_format=output_format)
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, AskModeResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> AsyncGenerator[
        Union[ProgressMessage, StreamedThoughts, StreamedTokens, ResearchModeResponse],
        None,
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> AsyncGenerator[
        Union[ProgressMessage, StreamedThoughts, StreamedTokens], None
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> AsyncGenerator[
        Union[ProgressMessage, StreamedTokens, ResearchModeResponse], None
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[True] = True,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> AsyncGenerator[Union[ProgressMessage, StreamedTokens], None]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[True] = True,
    ) -> AsyncGenerator[
        Union[StreamedThoughts, StreamedTokens, ResearchModeResponse], None
    ]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[True] = True,
        include_final_state: Literal[False] = False,
    ) -> AsyncGenerator[Union[StreamedThoughts, StreamedTokens], None]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[True] = True,
    ) -> AsyncGenerator[Union[StreamedTokens, ResearchModeResponse], None]: ...

    @overload
    def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: Literal[False] = False,
        include_thoughts: Literal[False] = False,
        include_final_state: Literal[False] = False,
    ) -> AsyncGenerator[StreamedTokens, None]: ...

    async def research_stream(
        self,
        query: Union[str, list[ChatMessage]],
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        reasoning_prompt: Optional[str] = None,
        include_progress: bool = True,
        include_thoughts: bool = True,
        include_final_state: bool = True,
    ):
        """Run the Query Agent research mode and stream the response.

        Args:
            query: The natural language query string or list of chat messages.
            collections: The collections to query. Overrides any collections
                provided in the constructor when set.
            reasoning_prompt: Optional prompt to control the agent's behavior during the
                research phase, guiding how it searches, retrieves, and reasons about data.
                The constructor's ``system_prompt`` controls the final response formatting.
            include_progress: Whether to include progress messages in the stream. These are informational messages about the progress of the agent's search.
            include_thoughts: Whether to include streamed thoughts in the stream. These are token deltas of the agent's reasoning process as it performs the research.
            include_final_state: Whether to include the final state in the stream. This is the final response class, ``ResearchModeResponse``, that will be the last item in the stream.

        Returns:
            A generator of the response stream.
            The generator will yield the following types:

            - [:class:`~weaviate_agents.query.classes.response.ProgressMessage`]: Informational messages about the progress of the agent's search (if ``include_progress`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.StreamedThoughts`]: Token deltas of the agent's reasoning process as it performs the research (if ``include_thoughts`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.ResearchModeResponse`]: The final response class that will be the last item in the stream (if ``include_final_state`` is ``True``).
            - [:class:`~weaviate_agents.query.classes.response.StreamedTokens`]: Token deltas from the agent's response.

        Examples:
            >>> from weaviate_agents import AsyncQueryAgent
            >>> from weaviate_agents.classes import StreamedThoughts, StreamedTokens, ProgressMessage, ResearchModeResponse
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> async for result in agent.research_stream("What are the terms of the contract signed by John Smith in May 2025?"):
            ...     if isinstance(result, ResearchModeResponse):
            ...         result.display()
            ...     elif isinstance(result, StreamedThoughts):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, StreamedTokens):
            ...         print(result.delta, end='', flush=True)
            ...     elif isinstance(result, ProgressMessage):
            ...         print(result.message)
        """
        request_body = self._prepare_research_mode_request_body(
            query=query,
            collections=collections,
            reasoning_prompt=reasoning_prompt,
            include_progress=include_progress,
            include_thoughts=include_thoughts,
            include_final_state=include_final_state,
        )
        async with httpx.AsyncClient() as client:
            async with aconnect_sse(
                client=client,
                method="POST",
                url=self.query_url + "/stream_research",
                json=request_body,
                headers=self._headers,
                timeout=self._timeout,
            ) as events:
                if events.response.is_error:
                    await events.response.aread()
                    raise Exception(events.response.text)

                async for sse in events.aiter_sse():
                    output = _parse_sse(sse, mode="research")
                    if isinstance(output, ProgressMessage):
                        if include_progress:
                            yield output
                    elif isinstance(output, StreamedThoughts):
                        if include_thoughts:
                            yield output
                    elif isinstance(output, ResearchModeResponse):
                        if include_final_state:
                            yield output
                    else:
                        yield output

    async def search(
        self,
        query: Union[str, list[ChatMessage]],
        limit: int = 20,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        filtering: Optional[Literal["recall", "precision"]] = None,
        diversity_weight: Optional[float] = None,
    ) -> AsyncSearchModeResponse:
        """Run the Query Agent search-only mode.

        This method sends the initial search request and returns an
        `AsyncSearchModeResponse` containing the first page of results. To
        paginate, use the `AsyncSearchModeResponse.next()` method. This reuses
        the same underlying searches to ensure a consistent result set across
        pages.

        Args:
            query: The natural language query string for the agent.
            limit: The maximum number of results to return for the first page.
            collections: The collections to query. Overrides any collections
                provided in the constructor when set.
            filtering: The filtering strategy to use for this search.
                Use "recall" to optimize for finding all relevant results,
                or "precision" to optimize for the accuracy of returned results.
                Defaults to "recall".
            diversity_weight: Optional float between 0.0 and 1.0 to diversify
                results with MMR reranking.
                Higher values push for more topical variety at the cost of relevance.
                Defaults to None (no diversity).

        Returns:
            An instance of :class:`~weaviate_agents.query.classes.response.AsyncSearchModeResponse` for the first page of results. Use
            the ``await response.next(limit=..., offset=...)`` method to paginate.

        Examples:
            >>> from weaviate_agents import AsyncQueryAgent
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> await agent.search("Find all NDAs signed by Jane Doe in 2024.")

            >>> from weaviate_agents import AsyncQueryAgent
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> # With pagination
            >>> page_1 = await agent.search("Find all NDAs signed by Jane Doe in 2024.", limit = 5)
            >>> page_2 = await page_1.next(limit = 5, offset = 5)
            >>> page_3 = await page_2.next(limit = 5, offset = 10)
        """
        collections = collections or self._collections
        if not collections:
            raise ValueError("No collections provided to the query agent.")
        searcher = AsyncQueryAgentSearcher(
            headers=self._headers,
            connection_headers=self._connection.additional_headers,
            timeout=self._timeout,
            query_url=self.query_url,
            query=query,
            collections=collections,
            system_prompt=self._system_prompt,
            filtering=filtering,
            diversity_weight=diversity_weight,
        )
        return await searcher.run(limit=limit)

    async def suggest_queries(
        self,
        collections: Union[list[Union[str, QueryAgentCollectionConfig]], None] = None,
        num_queries: int = 3,
        instructions: Optional[str] = None,
    ) -> SuggestQueryResponse:
        """Suggest queries for the data in your collections.

        Uses the agent to generate example queries that can be run against the given collections.

        This can help users discover what kinds of questions they can ask or generate example prompts for a dataset.

        Args:
            collections:
                Optional override for the collections configured at instantiation.
                Can be a list of collection names (str) or QueryAgentCollectionConfig objects.
            num_queries:
                The number of queries to suggest (default: 3).
            instructions:
                Optional natural language guidance for the style, topic, or language of the suggested queries.
                This is supplied in addition to the agent's system instructions.

        Returns:
            An instance of :class:`~weaviate_agents.query.classes.response.SuggestQueryResponse` which
            contains a list of suggested queries, with additional metadata if present.

        Examples:
            >>> from weaviate_agents import AsyncQueryAgent
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> await agent.suggest_queries(
            ...     collections=["Products"],
            ...     num_queries=5,
            ...     instructions="Focus on questions about eco-friendly features.",
            ... )

            >>> from weaviate_agents import AsyncQueryAgent
            >>> agent = AsyncQueryAgent(
            ...     client=client,
            ...     collections=["FinancialContracts"],
            ... )
            >>> await agent.suggest_queries(
            ...     collections=["FinancialContracts"],
            ...     num_queries=1,
            ...     instructions="Write your question in Spanish.",
            ... )
        """
        resolved_collections = collections or self._collections
        if not resolved_collections:
            raise ValueError("No collections provided to the query agent.")

        request_body: dict[str, Any] = {
            "collections": [
                (
                    collection
                    if isinstance(collection, str)
                    else collection.model_dump(mode="json")
                )
                for collection in resolved_collections
            ],
            "num_queries": num_queries,
            "headers": self._connection.additional_headers,
        }
        if instructions is not None:
            request_body["instructions"] = instructions

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.query_url + "/suggest_queries",
                headers=self._headers,
                json=request_body,
                timeout=self._timeout,
            )

            if response.is_error:
                raise Exception(response.text)

            return SuggestQueryResponse(**response.json())


@overload
def _parse_sse(
    sse: ServerSentEvent,
    mode: Literal["query"],
    output_format: Union[dict[str, Any], type[BaseModel], None] = None,
) -> Union[ProgressMessage, StreamedTokens, QueryAgentResponse]: ...


@overload
def _parse_sse(
    sse: ServerSentEvent,
    mode: Literal["research"],
    output_format: Union[dict[str, Any], type[BaseModel], None] = None,
) -> Union[ProgressMessage, StreamedThoughts, StreamedTokens, ResearchModeResponse]: ...


@overload
def _parse_sse(
    sse: ServerSentEvent, mode: Literal["ask"], output_format: dict[str, Any]
) -> Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[dict]]: ...


@overload
def _parse_sse(
    sse: ServerSentEvent, mode: Literal["ask"], output_format: type[M]
) -> Union[ProgressMessage, StreamedTokens, ParsedAskModeResponse[M]]: ...


@overload
def _parse_sse(
    sse: ServerSentEvent, mode: Literal["ask"], output_format: None
) -> Union[ProgressMessage, StreamedTokens, AskModeResponse]: ...


def _parse_sse(
    sse: ServerSentEvent,
    mode: Literal["query", "ask", "research"],
    output_format: Union[dict[str, Any], type[BaseModel], None] = None,
) -> Union[
    ProgressMessage,
    StreamedThoughts,
    StreamedTokens,
    QueryAgentResponse,
    AskModeResponse,
    ParsedAskModeResponse[Any],
    ResearchModeResponse,
]:
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
    elif sse.event == "streamed_thoughts":
        return StreamedThoughts.model_validate(data)
    elif sse.event == "final_state":
        if mode == "query":
            return QueryAgentResponse.model_validate(data)
        elif mode == "ask":
            return _parse_ask_result(
                response=data,
                output_format=output_format,
            )
        elif mode == "research":
            return ResearchModeResponse.model_validate(data)
    else:
        raise Exception(
            f"Unrecognised event type in response: {sse.event=}, {sse.data=}"
        )


def _parse_ask_result(
    response: dict[str, Any],
    output_format: Union[dict[str, Any], type[BaseModel], None],
) -> Union[AskModeResponse, ParsedAskModeResponse[Any]]:
    # Not overloaded: callers pass the broad union, and the precise return
    # type (ParsedAskModeResponse[M]) is conveyed by the public ask overloads.
    if isinstance(output_format, type) and issubclass(output_format, BaseModel):
        response["final_answer_parsed"] = output_format.model_validate_json(
            response["final_answer"]
        )
        return ParsedAskModeResponse[BaseModel](**response)

    elif isinstance(output_format, dict):
        try:
            response["final_answer_parsed"] = loads(response["final_answer"])
        except JSONDecodeError:
            warnings.warn(
                "Unable to decode final answer as dictionary, returning as string"
            )
            response["final_answer_parsed"] = response["final_answer"]
        return ParsedAskModeResponse[dict](**response)

    return AskModeResponse(**response)
