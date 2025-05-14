from enum import Enum
from typing import Any, Literal, Optional, Union
import warnings

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    filter_type: Literal["integer"] = Field(repr=False, default="integer")

    property_name: str
    operator: ComparisonOperator
    value: float


class IntegerArrayPropertyFilter(BaseModel):
    """Filter numeric-array properties using comparison operators."""

    filter_type: Literal["integer_array"] = Field(repr=False, default="integer_array")

    property_name: str
    operator: ComparisonOperator
    value: list[float]


class TextPropertyFilter(BaseModel):
    """Filter text properties using equality or LIKE operators"""

    filter_type: Literal["text"] = Field(repr=False, default="text")

    property_name: str
    operator: ComparisonOperator
    value: str


class TextArrayPropertyFilter(BaseModel):
    """Filter text-array properties using equality or LIKE operators"""

    filter_type: Literal["text_array"] = Field(repr=False, default="text_array")

    property_name: str
    operator: ComparisonOperator
    value: list[str]


class BooleanPropertyFilter(BaseModel):
    """Filter boolean properties using equality operators"""

    filter_type: Literal["boolean"] = Field(repr=False, default="boolean")

    property_name: str
    operator: ComparisonOperator
    value: bool


class BooleanArrayPropertyFilter(BaseModel):
    """Filter boolean-array properties using equality operators"""

    filter_type: Literal["boolean_array"] = Field(repr=False, default="boolean_array")

    property_name: str
    operator: ComparisonOperator
    value: list[bool]


class DatePropertyFilter(BaseModel):
    """Filter datetime properties using equality operators"""

    filter_type: Literal["date"] = Field(repr=False, default="date")

    property_name: str
    operator: ComparisonOperator
    value: str


class DateArrayPropertyFilter(BaseModel):
    """Filter datetime properties using equality operators"""

    filter_type: Literal["date_array"] = Field(repr=False, default="date_array")

    property_name: str
    operator: ComparisonOperator
    value: list[str]


class GeoPropertyFilter(BaseModel):
    """Filter geo-coordinates properties"""

    filter_type: Literal["geo"] = Field(repr=False, default="geo")

    property_name: str
    latitude: float
    longitude: float
    max_distance_meters: float


KNOWN_FILTER_TYPES = {
    "integer",
    "integer_array",
    "text",
    "text_array",
    "boolean",
    "boolean_array",
    "date",
    "date_array",
    "geo",
}


class UnknownPropertyFilter(BaseModel):
    """Catch-all filter for unknown filter types, to preserve future back-compatibility."""

    model_config = ConfigDict(extra="allow")
    filter_type: str

    @field_validator("filter_type", mode="after")
    @classmethod
    def ensure_filter_type_unknown(cls, value: str) -> str:
        if value in KNOWN_FILTER_TYPES:
            raise ValueError(
                f"{value} is an known filter type, but validation failed, "
                "so the response was not as expected. "
                "Try upgrading the weaviate-agents package to a new version."
            )
        return value
    
    def model_post_init(self, context: Any) -> None:
        warnings.warn(
            f"The filter_type {self.filter_type} wasn't recognised. "
            "Try upgrading the weaviate-agents package to a new version."
        )


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
    UnknownPropertyFilter,
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


class DateMetrics(str, Enum):
    COUNT = "COUNT"
    MAX = "MAXIMUM"
    MEDIAN = "MEDIAN"
    MIN = "MINIMUM"
    MODE = "MODE"


class IntegerPropertyAggregation(BaseModel):
    """Aggregate numeric properties using statistical functions"""

    aggregation_type: Literal["integer"] = "integer"

    property_name: str
    metrics: NumericMetrics


class TextPropertyAggregation(BaseModel):
    """Aggregate text properties using frequency analysis"""

    aggregation_type: Literal["text"] = "text"

    property_name: str
    metrics: TextMetrics
    top_occurrences_limit: Optional[int] = None


class BooleanPropertyAggregation(BaseModel):
    """Aggregate boolean properties using statistical functions"""

    aggregation_type: Literal["boolean"] = "boolean"

    property_name: str
    metrics: BooleanMetrics


class DatePropertyAggregation(BaseModel):
    """Aggregate datetime properties using statistical functions."""

    aggregation_type: Literal["date"] = "date"

    property_name: str
    metrics: DateMetrics


KNOWN_AGGREGATION_TYPES = {"integer", "text", "boolean", "date"}


class UnknownPropertyAggregation(BaseModel):
    """Catch-all aggregation for unknown aggregation types, to preserve future back-compatibility."""

    model_config = ConfigDict(extra="allow")
    aggregation_type: str

    @field_validator("aggregation_type", mode="after")
    @classmethod
    def ensure_filter_type_unknown(cls, value: str) -> str:
        if value in KNOWN_AGGREGATION_TYPES:
            raise ValueError(
                f"{value} is an known aggregation type, but validation failed, "
                "so the response was not as expected. "
                "Try upgrading the weaviate-agents package to a new version."
            )
        return value
    
    def model_post_init(self, context: Any) -> None:
        warnings.warn(
            f"The aggregation_type {self.aggregation_type} wasn't recognised. "
            "Try upgrading the weaviate-agents package to a new version."
        )


PropertyAggregationType = Union[
    IntegerPropertyAggregation,
    TextPropertyAggregation,
    BooleanPropertyAggregation,
    DatePropertyAggregation,
    UnknownPropertyAggregation,
]


class AggregationResult(BaseModel):
    """
    The aggregations to be performed on a collection in a vector database.

    They should be based on the original user query and can include multiple
    aggregations across different properties and metrics.
    """

    search_query: Optional[str] = None
    groupby_property: Optional[str] = None
    aggregations: list[PropertyAggregationType]
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
