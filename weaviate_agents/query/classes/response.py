from enum import Enum
from typing import Dict, Literal, Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from pydantic import BaseModel

console = Console()


class CollectionDescription(BaseModel):
    name: str
    description: str


class ComparisonOperator(str, Enum):
    EQUALS = "="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    NOT_EQUALS = "!="
    LIKE = "LIKE"


class IntegerPropertyFilter(BaseModel):
    """Filter numeric properties using comparison operators."""

    property_name: str
    operator: ComparisonOperator
    value: float


class TextPropertyFilter(BaseModel):
    """Filter text properties using equality or LIKE operators"""

    property_name: str
    operator: ComparisonOperator
    value: str


class BooleanPropertyFilter(BaseModel):
    """Filter boolean properties using equality operators"""

    property_name: str
    operator: ComparisonOperator
    value: bool


class QueryResult(BaseModel):
    queries: list[str]
    filters: list[
        list[Union[BooleanPropertyFilter, IntegerPropertyFilter, TextPropertyFilter]]
    ] = []
    filter_operators: Literal["AND", "OR"]


class NumericMetrics(str, Enum):
    COUNT = "COUNT"
    MAX = "MAXIMUM"
    MEAN = "MEAN"
    MEDIAN = "MEDIAN"
    MIN = "MINIMUM"
    MODE = "MODE"
    SUM = "SUM"
    TYPE = "TYPE"


class TextMetrics(str, Enum):
    COUNT = "COUNT"
    TYPE = "TYPE"
    TOP_OCCURRENCES = "TOP_OCCURRENCES"


class BooleanMetrics(str, Enum):
    COUNT = "COUNT"
    TYPE = "TYPE"
    TOTAL_TRUE = "TOTAL_TRUE"
    TOTAL_FALSE = "TOTAL_FALSE"
    PERCENTAGE_TRUE = "PERCENTAGE_TRUE"
    PERCENTAGE_FALSE = "PERCENTAGE_FALSE"


class IntegerPropertyAggregation(BaseModel):
    """Aggregate numeric properties using statistical functions"""

    property_name: str
    metrics: NumericMetrics


class TextPropertyAggregation(BaseModel):
    """Aggregate text properties using frequency analysis"""

    property_name: str
    metrics: TextMetrics
    top_occurrences_limit: Optional[int] = None


class BooleanPropertyAggregation(BaseModel):
    """Aggregate boolean properties using statistical functions"""

    property_name: str
    metrics: BooleanMetrics


class AggregationResult(BaseModel):
    """
    The aggregations to be performed on a collection in a vector database.

    They should be based on the original user query and can include multiple
    aggregations across different properties and metrics.
    """

    search_query: Optional[str] = None
    groupby_property: Optional[str] = None
    aggregations: list[
        Union[
            IntegerPropertyAggregation,
            TextPropertyAggregation,
            BooleanPropertyAggregation,
        ]
    ]
    filters: list[
        Union["BooleanPropertyFilter", "IntegerPropertyFilter", "TextPropertyFilter"]
    ] = []


class Usage(BaseModel):
    requests: Union[int, str] = 0
    request_tokens: Union[int, str, None] = None
    response_tokens: Union[int, str, None] = None
    total_tokens: Union[int, str, None] = None
    details: Union[Dict[str, int], Dict[str, str], None] = None


class AggregationResultWithCollection(AggregationResult):
    collection: str


class QueryResultWithCollection(QueryResult):
    collection: str


class Source(BaseModel):
    object_id: str
    collection: str


def print_query_agent_response(response: "QueryAgentResponse") -> None:
    """Prints a formatted response from the Query Agent using rich."""

    console.print(
        Panel(
            response.original_query,
            title="🔍 Original Query",
            padding=1,
        )
    )

    console.print(
        Panel(response.final_answer, title="📝 Final Answer", style="cyan", padding=1)
    )

    for collection_searches in response.searches:
        for i, result in enumerate(collection_searches):
            console.print(
                Panel(
                    Pretty(result),
                    title=f"🔭 Searches Executed {i+1}/{len(collection_searches)}",
                    style="white",
                    padding=1,
                )
            )
    if len(response.searches) == 0:
        console.print(Panel("🔭 No Searches Run", style="indian_red", padding=1))

    for collection_aggs in response.aggregations:
        for i, agg in enumerate(collection_aggs):
            console.print(
                Panel(
                    Pretty(agg),
                    title=f"📊 Aggregations Run {i+1}/{len(collection_aggs)}",
                    style="white",
                    padding=1,
                )
            )
    if len(response.aggregations) == 0:
        console.print(Panel("📊 No Aggregations Run", style="indian_red", padding=1))

    if response.missing_information:
        title = (
            "⚠️ Answer is Partial - Missing Information:"
            if response.is_partial_answer
            else "⚠️ Missing Information:"
        )
        missing_info = []
        for missing in response.missing_information:
            missing_info.append(f"- {missing}")

        console.print(
            Panel("\n".join(missing_info), title=title, style="yellow", padding=1)
        )

    sources = []
    for source in response.sources:
        sources.append(f" - {source}")
    if sources:
        console.print(
            Panel("\n".join(sources), title="📚 Sources", style="white", padding=1)
        )

    print("\n")

    table = Table(title="📊 Usage Statistics", show_header=False)
    table.add_row("LLM Requests:", str(response.usage.requests))
    table.add_row("Input Tokens:", str(response.usage.request_tokens))
    table.add_row("Output Tokens:", str(response.usage.response_tokens))
    table.add_row("Total Tokens:", str(response.usage.total_tokens))
    console.print(table)

    console.print(
        f"\n[bold]Total Time Taken:[/bold] {response.total_time:.2f}s", style="cyan"
    )


class QueryAgentResponse(BaseModel):
    original_query: str
    collection_names: list[str]
    searches: list[list[QueryResultWithCollection]]
    aggregations: list[list[AggregationResultWithCollection]]
    usage: Usage
    total_time: float
    aggregation_answer: Optional[str] = None
    has_aggregation_answer: bool
    has_search_answer: bool
    is_partial_answer: bool
    missing_information: list[str]
    final_answer: str
    sources: list[Source]

    def display(self) -> None:
        """
        Display a pretty-printed summary of the QueryAgentResponse object.

        Returns:
            None
        """

        print_query_agent_response(self)
        return None
