from __future__ import annotations

from typing import Any, Optional, Union

import httpx

from weaviate_agents.query.classes.collection import QueryAgentCollectionConfig
from weaviate_agents.query.classes.request import (
    SearchModeExecutionRequest,
    SearchModeGenerationRequest,
)
from weaviate_agents.query.classes.response import (
    QueryResultWithCollection,
    SearchModeResponseBase,
)


class _BaseQueryAgentSearcher:
    def __init__(
        self,
        headers: dict[str, Any],
        connection_headers: dict[str, str],
        timeout: int,
        agent_url: str,
        query: str,
        collections: list[Union[str, QueryAgentCollectionConfig]],
        system_prompt: Optional[str],
    ):
        self.headers = headers
        self.connection_headers = connection_headers
        self.timeout = timeout
        self.agent_url = agent_url
        self.query = query
        self.collections = collections
        self.system_prompt = system_prompt
        self._cached_searches: Optional[list[QueryResultWithCollection]] = None

    def _get_request_body(self, limit: int, offset: int) -> dict[str, Any]:
        if self._cached_searches is None:
            return SearchModeGenerationRequest(
                headers=self.connection_headers,
                original_query=self.query,
                collections=self.collections,
                limit=limit,
                offset=offset,
                system_prompt=self.system_prompt,
            ).model_dump(mode="json")
        else:
            return SearchModeExecutionRequest(
                headers=self.connection_headers,
                original_query=self.query,
                collections=self.collections,
                limit=limit,
                offset=offset,
                searches=self._cached_searches,
            ).model_dump(mode="json")


class QueryAgentSearcher(_BaseQueryAgentSearcher):
    """A configured searcher for the Query Agent search-only mode.

    This configured search can be run using the `run` method. This allows you to
    paginate through the results set multiple times with different `limit` / `offset`
    values. This will result in the same underlying searches being performed each time,
    resulting in a consistent results set across pages.

    Warning:
        Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query)
    """

    def _handle_response(self, response: httpx.Response) -> SearchModeResponse:
        if response.is_error:
            raise Exception(response.text)

        parsed_response = SearchModeResponse(**response.json())
        if parsed_response.searches:
            self._cached_searches = parsed_response.searches
        parsed_response._searcher = self
        return parsed_response

    def run(self, limit: int = 20, offset: int = 0) -> SearchModeResponse:
        """Run the search-only agent with the given `limit` and `offset` values.

        Calling this method multiple times on the same QueryAgentSearcher instance will result
        in the same underlying searches being performed each time, allowing you to paginate
        over a consistent results set.

        Args:
            limit: The maximum number of results to return. If not specified, this defaults to 20.
            offset: The offset to start from. If not specified, the retrieval begins from the first object in the results set.

        Returns:
            A `SearchModeResponse` object containing the results of the search, the usage, and the underlying searches performed.
        """
        request_body = self._get_request_body(limit, offset)
        response = httpx.post(
            self.agent_url + "/search_only",
            headers=self.headers,
            json=request_body,
            timeout=self.timeout,
        )
        return self._handle_response(response)


class AsyncQueryAgentSearcher(_BaseQueryAgentSearcher):
    """A configured async searcher for the Query Agent search-only mode.

    This configured search can be run using the `run` method. This allows you to
    paginate through the results set multiple times with different `limit` / `offset`
    values. This will result in the same underlying searches being performed each time,
    resulting in a consistent results set across pages.

    Warning:
        Weaviate Agents - Query Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query)
    """

    def _handle_response(self, response: httpx.Response) -> AsyncSearchModeResponse:
        if response.is_error:
            raise Exception(response.text)

        parsed_response = AsyncSearchModeResponse(**response.json())
        if parsed_response.searches:
            self._cached_searches = parsed_response.searches
        parsed_response._searcher = self
        return parsed_response

    async def run(self, limit: int = 20, offset: int = 0) -> AsyncSearchModeResponse:
        """Run the search-only agent with the given `limit` and `offset` values.

        Calling this method multiple times on the same AsyncQueryAgentSearcher instance will result
        in the same underlying searches being performed each time, allowing you to paginate
        over a consistent results set.

        Args:
            limit: The maximum number of results to return. If not specified, this defaults to 20.
            offset: The offset to start from. If not specified, the retrieval begins from the first object in the results set.

        Returns:
            An `AsyncSearchModeResponse` object containing the results of the search, the usage, and the underlying searches performed.
        """
        request_body = self._get_request_body(limit, offset)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.agent_url + "/search_only",
                headers=self.headers,
                json=request_body,
                timeout=self.timeout,
            )
        return self._handle_response(response)


class SearchModeResponse(SearchModeResponseBase[QueryAgentSearcher]):
    """Reponse for the Query Agent search-only mode.

    This contains the results of the search, the usage, and the underlying
    searches performed. You can paginate through the results set by calling
    the `next` method on this reponse with different `limit` / `offset` values.
    This will result in the same underlying searches being performed each time,
    resulting in a consistent results set across pages.
    """

    def next(self, limit: int = 20, offset: int = 0) -> SearchModeResponse:
        """Paginate the search-only results with the given `limit` and `offset` values.

        Args:
            limit: The maximum number of results to return. If not specified, this defaults to 20.
            offset: The offset to start from. If not specified, the retrieval begins from the first object in the results set.

        Returns:
            The next `SearchModeResponse` page.
        """
        return self._searcher.run(limit=limit, offset=offset)


class AsyncSearchModeResponse(SearchModeResponseBase[AsyncQueryAgentSearcher]):
    """Reponse for the Query Agent search-only mode.

    This contains the results of the search, the usage, and the underlying
    searches performed. You can paginate through the results set by calling
    the `next` method on this reponse with different `limit` / `offset` values.
    This will result in the same underlying searches being performed each time,
    resulting in a consistent results set across pages.
    """

    async def next(self, limit: int = 20, offset: int = 0) -> AsyncSearchModeResponse:
        """Paginate the search-only results with the given `limit` and `offset` values.

        Args:
            limit: The maximum number of results to return. If not specified, this defaults to 20.
            offset: The offset to start from. If not specified, the retrieval begins from the first object in the results set.

        Returns:
            The next `SearchModeResponse` page.
        """
        return await self._searcher.run(limit=limit, offset=offset)
