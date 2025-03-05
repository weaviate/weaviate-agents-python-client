from typing import Union

from weaviate.client import WeaviateClient


class _BaseAgent:
    """
    Base class for all agents.
    """

    def __init__(
        self,
        client: WeaviateClient,
        agents_host: Union[str, None] = None,
    ):
        """
        Initialize the base agent.

        Args:
            client: A Weaviate client instance, either sync or async.
            agents_host: Optional host URL for the agents service. If not provided,
                will use the default agents host.
        """
        self._client = client
        self._connection = client._connection
        self._agents_host = agents_host or "https://api.agents.weaviate.io"

        self._headers = {
            "Authorization": self._connection.get_current_bearer_token(),
            "X-Weaviate-Cluster-Url": self._client._connection.url.replace(":443", ""),
        }
