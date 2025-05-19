from typing import Generic, TypeVar, Union

from weaviate.client import WeaviateAsyncClient, WeaviateClient

ClientType = TypeVar("ClientType", bound=Union[WeaviateClient, WeaviateAsyncClient])
"""Type variable for Weaviate client, :class:`~weaviate.WeaviateClient` or :class:`~weaviate.WeaviateAsyncClient`."""


class _BaseAgent(Generic[ClientType]):
    """Base class for all agents."""

    def __init__(
        self,
        client: ClientType,
        agents_host: Union[str, None] = None,
    ):
        """Initialize the base agent.

        Args:
            client: A Weaviate client instance, either sync or async.
            agents_host: Optional host URL for the agents service. If not provided,
                will use the default agents host.
        """
        self._client: ClientType = client
        self._connection = client._connection
        self._agents_host = agents_host or "https://api.agents.weaviate.io"

        self._headers = {
            "Authorization": self._connection.get_current_bearer_token(),
            "X-Weaviate-Cluster-Url": self._client._connection.url.replace(":443", ""),
        }
