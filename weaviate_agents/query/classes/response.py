from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, RootModel

from weaviate_agents.classes.core import Usage
from weaviate_agents.utils import print_query_agent_response


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
    CONTAINS_ANY = "contains_any"
    CONTAINS_ALL = "contains_all"


class IntegerPropertyFilter(BaseModel):
    """Filter numeric properties using comparison operators."""
    
    filter_type: Literal["integer"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: float


class IntegerArrayPropertyFilter(BaseModel):
    """Filter numeric-array properties using comparison operators."""

    filter_type: Literal["integer_array"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: list[float]


class TextPropertyFilter(BaseModel):
    """Filter text properties using equality or LIKE operators"""

    filter_type: Literal["text"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: str


class TextArrayPropertyFilter(BaseModel):
    """Filter text-array properties using equality or LIKE operators"""

    filter_type: Literal["text_array"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: list[str]


class BooleanPropertyFilter(BaseModel):
    """Filter boolean properties using equality operators"""

    filter_type: Literal["boolean"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: bool


class BooleanArrayPropertyFilter(BaseModel):
    """Filter boolean-array properties using equality operators"""

    filter_type: Literal["boolean_array"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: list[bool]


class DatePropertyFilter(BaseModel):
    """Filter datetime properties using equality operators"""

    filter_type: Literal["date"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: str


class DateArrayPropertyFilter(BaseModel):
    """Filter datetime properties using equality operators"""

    filter_type: Literal["date_array"] = Field(repr=False)

    property_name: str
    operator: ComparisonOperator
    value: str


class GeoPropertyFilter(BaseModel):
    """Filter geo-coordinates properties"""

    filter_type: Literal["geo"] = Field(repr=False)

    property_name: str
    latitude: float
    longitude: float
    max_distance_meters: float


PropertyFilterType = Union[
    IntegerPropertyFilter,
    IntegerArrayPropertyFilter,
    TextPropertyFilter,
    TextArrayPropertyFilter,
    BooleanPropertyFilter,
    BooleanArrayPropertyFilter,
    DatePropertyFilter,
    DateArrayPropertyFilter,
    GeoPropertyFilter,
]


class QueryResult(BaseModel):
    queries: list[str]
    filters: list[list[PropertyFilterType]] = []
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
    filters: list[PropertyFilterType] = []


class AggregationResultWithCollection(AggregationResult):
    collection: str


class QueryResultWithCollection(QueryResult):
    collection: str


class Source(BaseModel):
    object_id: str
    collection: str


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
