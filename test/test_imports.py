"""Tests for verifying correct package imports and public API exposure."""


def test_package_imports():
    """Test that all public modules and classes can be imported correctly.

    This test verifies that the essential modules, classes and functions from
    weaviate_agents are properly exposed and can be imported through the public API.
    """
    # Test direct imports from the package
    import weaviate_agents
    from weaviate_agents.classes.query import CollectionDescription, QueryAgentResponse
    from weaviate_agents.errors import QueryAgentError
    from weaviate_agents.query import QueryAgent

    # Verify the imported items are the correct types
    assert isinstance(
        CollectionDescription, type
    ), "CollectionDescription should be a class"
    assert isinstance(QueryAgentResponse, type), "QueryAgentResponse should be a class"
    assert isinstance(QueryAgentError, type), "QueryAgentError should be a class"
    assert isinstance(QueryAgent, type), "QueryAgent should be a class"

    # Optional: Test that __all__ is defined and contains expected modules
    if hasattr(weaviate_agents, "__all__"):
        expected_modules = {
            "base",
            "classes",
            "errors",
            "personalization",
            "query",
            "transformation",
            "utils",
        }
        assert (
            set(weaviate_agents.__all__) == expected_modules
        ), "Package __all__ should contain all public modules"
