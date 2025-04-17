from typing import Optional
from uuid import UUID

import httpx
from weaviate.classes.config import DataType
from weaviate.client import WeaviateClient
from weaviate.collections.classes.filters import _Filters

from weaviate_agents.base import _BaseAgent
from weaviate_agents.personalization.classes import (
    GetObjectsRequest,
    Persona,
    PersonaInteraction,
    PersonaInteractionResponse,
    PersonalizationAgentGetObjectsResponse,
    PersonalizationRequest,
)
from weaviate_agents.personalization.query import PersonalizedQuery


class PersonalizationAgent(_BaseAgent):
    """An agent for personalizing search results and queries based on persona interactions.

    Warning:
        Weaviate Agents - Personalization Agent is an early stage alpha product. The API is subject to
        breaking changes. Please ensure you are using the latest version of the client.

        For more information, see the [Weaviate Agents - Personalization Agent Docs](https://weaviate.io/developers/agents/personalization)
    """

    def __init__(
        self,
        client: WeaviateClient,
        reference_collection: str,
        agents_host: Optional[str] = None,
        vector_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        super().__init__(client, agents_host)
        self._reference_collection = reference_collection
        self._vector_name = vector_name
        self._route = "/personalization"
        self._timeout = timeout

    @classmethod
    def create(
        cls,
        client: WeaviateClient,
        reference_collection: str,
        user_properties: Optional[dict[str, DataType]] = None,
        agents_host: Optional[str] = None,
        vector_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> "PersonalizationAgent":
        """Create a new Personalization Agent for a collection.

        Args:
            client: The Weaviate client
            reference_collection: The name of the collection to personalize
            user_properties: Optional dictionary of user properties and their data types
            agents_host: Optional host URL for the agents service
            timeout: Optional timeout for the request
        Returns:
            PersonalizationAgent: A new instance of the Personalization Agent
        """
        agent = cls(
            client=client,
            reference_collection=reference_collection,
            agents_host=agents_host,
            vector_name=vector_name,
        )
        agent._initialize(
            reference_collection,
            create=True,
            user_properties=user_properties,
            vector_name=vector_name,
            timeout=timeout,
        )
        return agent

    @classmethod
    def connect(
        cls,
        client: WeaviateClient,
        reference_collection: str,
        agents_host: Optional[str] = None,
        vector_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> "PersonalizationAgent":
        """Connect to an existing Personalization Agent for a collection.

        Args:
            client: The Weaviate client
            reference_collection: The name of the collection to connect to
            agents_host: Optional host URL for the agents service
            timeout: Optional timeout for the request
        Returns:
            PersonalizationAgent: An instance of the Personalization Agent
        """
        agent = cls(
            client=client,
            reference_collection=reference_collection,
            agents_host=agents_host,
            vector_name=vector_name,
        )
        agent._initialize(
            reference_collection, create=False, vector_name=vector_name, timeout=timeout
        )
        return agent

    def _initialize(
        self,
        reference_collection: str,
        create: bool = False,
        user_properties: Optional[dict[str, DataType]] = None,
        vector_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """Initialize the agent with the given reference collection and user properties.

        Args:
            reference_collection: The name of the collection to personalize
            user_properties: Optional dictionary of user properties and their data types
            vector_name: Optional name of the vector field to use
        """
        request_data = {
            "collection_name": reference_collection,
            "headers": self._connection.additional_headers,
            "persona_properties": user_properties or {},
            "item_collection_vector_name": vector_name,
            "create": create,
        }

        response = httpx.post(
            f"{self._agents_host}{self._route}/",
            headers=self._headers,
            json=request_data,
            timeout=timeout,
        )

        if response.is_error:
            raise Exception(
                f"Failed to initialize personalization agent: {response.text}"
            )

    def add_persona(self, persona: Persona) -> None:
        """Add a persona to the Personalization Agent's persona collection.

        Args:
            persona: The persona to add. The persona must have a persona_id and properties that match the user properties
            defined when the Personalization Agent was created.
        """

        request_data = {
            "persona": persona.model_dump(mode="json"),
            "personalization_request": {
                "collection_name": self._reference_collection,
                "headers": self._connection.additional_headers,
                "item_collection_vector_name": self._vector_name,
                "create": False,
            },
        }
        response = httpx.post(
            f"{self._agents_host}{self._route}/persona",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(f"Failed to add persona: {response.text}")

    def update_persona(self, persona: Persona) -> None:
        """Update an existing persona in the Personalization Agent's persona collection.

        Args:
            persona: The persona to update. The persona must have a persona_id and properties that match
                    the user properties defined when the Personalization Agent was created.
        """
        request_data = {
            "persona": persona.model_dump(mode="json"),
            "personalization_request": {
                "collection_name": self._reference_collection,
                "headers": self._connection.additional_headers,
                "item_collection_vector_name": self._vector_name,
                "create": False,
            },
        }
        response = httpx.put(
            f"{self._agents_host}{self._route}/persona",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )
        if response.is_error:
            raise Exception(f"Failed to update persona: {response.text}")

    def get_persona(self, persona_id: UUID) -> Persona:
        """Get a persona by persona_id from the Personalization Agent's persona collection.

        Args:
            persona_id: The ID of the persona to retrieve

        Returns:
            Persona: The retrieved persona
        """
        request_data = {
            "collection_name": self._reference_collection,
            "headers": self._connection.additional_headers,
            "item_collection_vector_name": self._vector_name,
            "create": False,
        }

        response = httpx.post(
            f"{self._agents_host}{self._route}/persona/{str(persona_id)}",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(f"Failed to get persona: {response.text}")

        return Persona(**response.json())

    def delete_persona(self, persona_id: UUID) -> None:
        """Delete a persona by persona_id from the Personalization Agent's persona collection.

        Args:
            persona_id: The ID of the persona to delete
        """
        request_data = {
            "collection_name": self._reference_collection,
            "headers": self._connection.additional_headers,
            "item_collection_vector_name": self._vector_name,
            "create": False,
        }

        response = httpx.post(
            f"{self._agents_host}{self._route}/persona/delete/{str(persona_id)}",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(f"Failed to delete persona: {response.text}")

    def has_persona(self, persona_id: UUID) -> bool:
        """Check if a persona exists in the Personalization Agent's persona collection.

        Args:
            persona_id: The ID of the persona to check

        Returns:
            bool: True if the persona exists, False otherwise
        """
        request_data = {
            "collection_name": self._reference_collection,
            "headers": self._connection.additional_headers,
            "item_collection_vector_name": self._vector_name,
            "create": False,
        }

        response = httpx.post(
            f"{self._agents_host}{self._route}/persona/{str(persona_id)}/exists",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(f"Failed to check persona existence: {response.text}")

        return response.json()["exists"]

    def add_interactions(
        self,
        interactions: list[PersonaInteraction],
        create_persona_if_not_exists: bool = True,
        remove_previous_interactions: bool = False,
    ) -> None:
        """Add interactions for personas to the Personalization Agent.

        Args:
            interactions: List of interactions to add. Each interaction can specify
                        `replace_previous_interactions=True` to replace that specific
                        item's interaction history.
            create_persona_if_not_exists: Whether to create personas that don't exist yet
            remove_previous_interactions: Whether to remove previous interactions for all items
                                       in the current batch. Setting this to True is equivalent
                                       to setting `replace_previous_interactions=True` for every
                                       interaction in the batch. Use with caution as it affects
                                       all items in the current batch.
        """
        request_data = {
            "interactions_request": {
                "interactions": [
                    interaction.model_dump(mode="json") for interaction in interactions
                ],
                "create_persona_if_not_exists": create_persona_if_not_exists,
                "remove_previous_interactions": remove_previous_interactions,
            },
            "personalization_request": {
                "collection_name": self._reference_collection,
                "headers": self._connection.additional_headers,
                "item_collection_vector_name": self._vector_name,
                "create": False,
            },
        }

        response = httpx.post(
            f"{self._agents_host}{self._route}/interactions",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(f"Failed to add interactions: {response.text}")

    def get_interactions(
        self, persona_id: UUID, interaction_type: str
    ) -> list[PersonaInteractionResponse]:
        """Get interactions for a specific persona filtered by interaction type.

        Args:
            persona_id: The ID of the persona to get interactions for
            interaction_type: The type of interaction to filter by (e.g. "positive", "negative")

        Returns:
            list[PersonaInteractionResponse]: List of matching interactions for the persona
        """
        request_data = {
            "interaction_request": {
                "persona_id": str(persona_id),
                "interaction_type": interaction_type,
            },
            "personalization_request": {
                "collection_name": self._reference_collection,
                "headers": self._connection.additional_headers,
                "item_collection_vector_name": self._vector_name,
                "create": False,
            },
        }

        response = httpx.post(
            f"{self._agents_host}{self._route}/interactions/get",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(f"Failed to get interactions: {response.text}")

        return [
            PersonaInteractionResponse(**interaction) for interaction in response.json()
        ]

    def get_objects(
        self,
        persona_id: UUID,
        limit: int = 10,
        recent_interactions_count: int = 100,
        exclude_interacted_items: bool = True,
        decay_rate: float = 0.1,
        exclude_items: list[str] = [],
        use_agent_ranking: bool = True,
        explain_results: bool = True,
        instruction: Optional[str] = None,
        filters: Optional[_Filters] = None,
    ) -> PersonalizationAgentGetObjectsResponse:
        """Get Personalized objects for a specific persona.

        Args:
            persona_id: The ID of the persona to get objects for
            limit: The maximum number of objects to return
            recent_interactions_count: The number of recent interactions to consider
        """
        objects_request = GetObjectsRequest(
            persona_id=persona_id,
            limit=limit,
            recent_interactions_count=recent_interactions_count,
            exclude_interacted_items=exclude_interacted_items,
            decay_rate=decay_rate,
            exclude_items=exclude_items,
            use_agent_ranking=use_agent_ranking,
            explain_results=explain_results,
            instruction=instruction,
            filters=filters,
        )
        request_data = {
            "objects_request": objects_request.model_dump(mode="json"),
            "personalization_request": {
                "collection_name": self._reference_collection,
                "headers": self._connection.additional_headers,
                "item_collection_vector_name": self._vector_name,
                "create": False,
            },
        }

        response = httpx.post(
            f"{self._agents_host}{self._route}/objects",
            headers=self._headers,
            json=request_data,
            timeout=self._timeout,
        )

        if response.is_error:
            raise Exception(f"Failed to get objects: {response.text}")

        return PersonalizationAgentGetObjectsResponse(**response.json())

    @classmethod
    def exists(
        cls,
        client: WeaviateClient,
        reference_collection: str,
        agents_host: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """Check if a persona collection exists for a given reference collection.

        Args:
            client: The Weaviate client
            reference_collection: The name of the collection to check
            agents_host: Optional host URL for the agents service
            timeout: Optional timeout for the request

        Returns:
            bool: True if the persona collection exists, False otherwise
        """
        # Initialize base values from client
        base_agent = cls(client, reference_collection, agents_host=agents_host)

        response = httpx.get(
            f"{base_agent._agents_host}{base_agent._route}/exists/{reference_collection}",
            headers=base_agent._headers,
            timeout=timeout,
        )

        if response.is_error:
            raise Exception(
                f"Failed to check if persona collection exists: {response.text}"
            )

        return response.json()["persona_collection_exists"]

    def query(
        self,
        persona_id: UUID,
        strength: float = 0.5,
        overfetch_factor: float = 1.5,
        recent_interactions_count: int = 100,
        decay_rate: float = 0.1,
    ) -> PersonalizedQuery:
        personalization_request = PersonalizationRequest(
            collection_name=self._reference_collection,
            headers=self._connection.additional_headers,
            item_collection_vector_name=self._vector_name,
            create=False,
        )
        return PersonalizedQuery(
            agents_host=self._agents_host,
            headers=self._headers,
            persona_id=persona_id,
            personalization_request=personalization_request,
            timeout=self._timeout,
            strength=strength,
            overfetch_factor=overfetch_factor,
            recent_interactions_count=recent_interactions_count,
            decay_rate=decay_rate,
        )
