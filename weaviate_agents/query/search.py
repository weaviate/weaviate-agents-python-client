from typing import Any, Optional, Union

import httpx

from weaviate_agents.query.classes.collection import QueryAgentCollectionConfig
from weaviate_agents.query.classes.request import (
    SearchModeExecutionRequest,
    SearchModeGenerationRequest,
)
from weaviate_agents.query.classes.response import (
    QueryResultWithCollection,
    SearchModeResponse,
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
        
    def _handle_response(self, response: httpx.Response) -> SearchModeResponse:
        if response.is_error:
            raise Exception(response.text)
        
        parsed_response = SearchModeResponse(**response.json())
        if parsed_response.searches:
            self._cached_searches = parsed_response.searches
        return parsed_response
        

class QueryAgentSearcher(_BaseQueryAgentSearcher):
    def execute(self, limit: int, offset: int) -> SearchModeResponse:
        request_body = self._get_request_body(limit, offset)
        response = httpx.post(
            self.agent_url + "/search_only",
            headers=self.headers,
            json=request_body,
            timeout=self.timeout,
        )
        return self._handle_response(response)
    

class AsyncQueryAgentSearcher(_BaseQueryAgentSearcher):
    async def execute(self, limit: int, offset: int) -> SearchModeResponse:
        request_body = self._get_request_body(limit, offset)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.agent_url + "/search_only",
                headers=self.headers,
                json=request_body,
                timeout=self.timeout,
            )
        return self._handle_response(response)
