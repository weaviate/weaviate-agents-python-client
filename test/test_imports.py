"""Tests for verifying correct package imports and public API exposure."""


def test_package_imports():
    """Test that all public modules and classes can be imported correctly.

    This test verifies that the essential modules, classes and functions from
    weaviate_agents are properly exposed and can be imported through the public API.
    """
    # Test direct imports from the package
    import weaviate_agents
    from weaviate_agents.classes.query import CollectionDescription, QueryAgentResponse
    from weaviate_agents.query import QueryAgent

    # Verify the imported items are the correct types
    assert isinstance(
        CollectionDescription, type
    ), "CollectionDescription should be a class"
    assert isinstance(QueryAgentResponse, type), "QueryAgentResponse should be a class"
    assert isinstance(QueryAgent, type), "QueryAgent should be a class"

    # Optional: Test that __all__ is defined and contains expected modules
    if hasattr(weaviate_agents, "__all__"):
        expected_modules = {
            "base",
            "classes",
            "personalization",
            "query",
            "transformation",
            "utils",
        }
        assert (
            set(weaviate_agents.__all__) == expected_modules
        ), "Package __all__ should contain all public modules"


def test_class_exports():
    """Test that all data model classes are properly exported through the classes module."""
    from weaviate_agents.classes import (
        AggregationResult,
        AggregationResultWithCollection,
        AppendPropertyOperation,
        BooleanMetrics,
        BooleanPropertyAggregation,
        BooleanPropertyFilter,
        CollectionDescription,
        ComparisonOperator,
        DependentOperationStep,
        IntegerPropertyAggregation,
        IntegerPropertyFilter,
        NumericMetrics,
        Operations,
        OperationStep,
        OperationType,
        QueryAgentResponse,
        QueryResult,
        QueryResultWithCollection,
        Source,
        TextMetrics,
        TextPropertyAggregation,
        TextPropertyFilter,
        UpdatePropertyOperation,
        Usage,
    )

    # Verify all exports are classes
    classes = [
        CollectionDescription,
        QueryAgentResponse,
        Source,
        ComparisonOperator,
        IntegerPropertyFilter,
        TextPropertyFilter,
        BooleanPropertyFilter,
        QueryResult,
        NumericMetrics,
        TextMetrics,
        BooleanMetrics,
        IntegerPropertyAggregation,
        TextPropertyAggregation,
        BooleanPropertyAggregation,
        AggregationResult,
        Usage,
        AggregationResultWithCollection,
        QueryResultWithCollection,
        OperationType,
        OperationStep,
        AppendPropertyOperation,
        UpdatePropertyOperation,
        DependentOperationStep,
        Operations,
    ]

    for cls in classes:
        assert isinstance(cls, type), f"{cls.__name__} should be a class"

    # Verify __all__ contains all exports
    import weaviate_agents.classes

    expected_exports = [
        "CollectionDescription",
        "QueryAgentResponse",
        "Source",
        "ComparisonOperator",
        "IntegerPropertyFilter",
        "TextPropertyFilter",
        "BooleanPropertyFilter",
        "QueryResult",
        "NumericMetrics",
        "TextMetrics",
        "BooleanMetrics",
        "IntegerPropertyAggregation",
        "TextPropertyAggregation",
        "BooleanPropertyAggregation",
        "AggregationResult",
        "Usage",
        "AggregationResultWithCollection",
        "QueryResultWithCollection",
        "OperationType",
        "OperationStep",
        "AppendPropertyOperation",
        "UpdatePropertyOperation",
        "DependentOperationStep",
        "Operations",
    ]

    assert hasattr(
        weaviate_agents.classes, "__all__"
    ), "Module should have __all__ defined"
    assert set(weaviate_agents.classes.__all__) == set(
        expected_exports
    ), "__all__ should contain all data model classes"
