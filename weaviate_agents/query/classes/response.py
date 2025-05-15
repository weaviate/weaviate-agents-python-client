import warnings
from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from weaviate_agents.classes.core import Usage
from weaviate_agents.utils import print_query_agent_response


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


class KnownFilterType(str, Enum):
    INTEGER = "integer"
    INTEGER_ARRAY = "integer_array"
    TEXT = "text"
    TEXT_ARRAY = "text_array"
    BOOLEAN = "boolean"
    BOOLEAN_ARRAY = "boolean_array"
    DATE = "date"
    DATE_ARRAY = "date_array"
    GEO = "geo"


class KnownPropertyFilterBase(BaseModel):
    filter_type: KnownFilterType
    property_name: str


class IntegerPropertyFilter(KnownPropertyFilterBase):
    """Filter numeric properties using comparison operators."""

    filter_type: Literal[KnownFilterType.INTEGER] = Field(
        repr=False, default=KnownFilterType.INTEGER
    )

    operator: ComparisonOperator
    value: float


class IntegerArrayPropertyFilter(KnownPropertyFilterBase):
    """Filter numeric-array properties using comparison operators."""

    filter_type: Literal[KnownFilterType.INTEGER_ARRAY] = Field(
        repr=False, default=KnownFilterType.INTEGER_ARRAY
    )

    operator: ComparisonOperator
    value: list[float]


class TextPropertyFilter(KnownPropertyFilterBase):
    """Filter text properties using equality or LIKE operators"""

    filter_type: Literal[KnownFilterType.TEXT] = Field(
        repr=False, default=KnownFilterType.TEXT
    )

    operator: ComparisonOperator
    value: str


class TextArrayPropertyFilter(KnownPropertyFilterBase):
    """Filter text-array properties using equality or LIKE operators"""

    filter_type: Literal[KnownFilterType.TEXT_ARRAY] = Field(
        repr=False, default=KnownFilterType.TEXT_ARRAY
    )

    operator: ComparisonOperator
    value: list[str]


class BooleanPropertyFilter(KnownPropertyFilterBase):
    """Filter boolean properties using equality operators"""

    filter_type: Literal[KnownFilterType.BOOLEAN] = Field(
        repr=False, default=KnownFilterType.BOOLEAN
    )

    operator: ComparisonOperator
    value: bool


class BooleanArrayPropertyFilter(KnownPropertyFilterBase):
    """Filter boolean-array properties using equality operators"""

    filter_type: Literal[KnownFilterType.BOOLEAN_ARRAY] = Field(
        repr=False, default=KnownFilterType.BOOLEAN_ARRAY
    )

    operator: ComparisonOperator
    value: list[bool]


class DatePropertyFilter(KnownPropertyFilterBase):
    """Filter datetime properties using equality operators"""

    filter_type: Literal[KnownFilterType.DATE] = Field(
        repr=False, default=KnownFilterType.DATE
    )

    operator: ComparisonOperator
    value: str


class DateArrayPropertyFilter(KnownPropertyFilterBase):
    """Filter datetime properties using equality operators"""

    filter_type: Literal[KnownFilterType.DATE_ARRAY] = Field(
        repr=False, default=KnownFilterType.DATE_ARRAY
    )

    operator: ComparisonOperator
    value: list[str]


class GeoPropertyFilter(KnownPropertyFilterBase):
    """Filter geo-coordinates properties"""

    filter_type: Literal[KnownFilterType.GEO] = Field(
        repr=False, default=KnownFilterType.GEO
    )

    latitude: float
    longitude: float
    max_distance_meters: float


class UnknownPropertyFilter(BaseModel):
    """Catch-all filter for unknown filter types, to preserve future back-compatibility."""

    model_config = ConfigDict(extra="allow")
    filter_type: None

    @field_validator("filter_type", mode="before")
    @classmethod
    def ensure_filter_type_unknown(cls, value: Any) -> None:
        if value in set(KnownFilterType):
            raise ValueError(
                f"{value} is an known filter type, but validation failed, "
                "so the response was not as expected. "
                "Try upgrading the weaviate-agents package to a new version."
            )
        return None

    def model_post_init(self, context: Any) -> None:
        warnings.warn(
            f"The filter_type {self.filter_type} wasn't recognised. "
            "Try upgrading the weaviate-agents package to a new version."
        )


PropertyFilter = Union[
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
    filters: list[list[PropertyFilter]] = []
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


class KnownAggregationType(str, Enum):
    INTEGER = "integer"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"


class KnownPropertyAggregationBase(BaseModel):
    aggregation_type: KnownAggregationType
    property_name: str


class IntegerPropertyAggregation(KnownPropertyAggregationBase):
    """Aggregate numeric properties using statistical functions"""

    aggregation_type: Literal[KnownAggregationType.INTEGER] = Field(
        repr=False, default=KnownAggregationType.INTEGER
    )
    metrics: NumericMetrics


class TextPropertyAggregation(KnownPropertyAggregationBase):
    """Aggregate text properties using frequency analysis"""

    aggregation_type: Literal[KnownAggregationType.TEXT] = Field(
        repr=False, default=KnownAggregationType.TEXT
    )
    metrics: TextMetrics
    top_occurrences_limit: Optional[int] = None


class BooleanPropertyAggregation(KnownPropertyAggregationBase):
    """Aggregate boolean properties using statistical functions"""

    aggregation_type: Literal[KnownAggregationType.BOOLEAN] = Field(
        repr=False, default=KnownAggregationType.BOOLEAN
    )
    metrics: BooleanMetrics


class DatePropertyAggregation(KnownPropertyAggregationBase):
    """Aggregate datetime properties using statistical functions."""

    aggregation_type: Literal[KnownAggregationType.DATE] = Field(
        repr=False, default=KnownAggregationType.DATE
    )
    metrics: DateMetrics


class UnknownPropertyAggregation(BaseModel):
    """Catch-all aggregation for unknown aggregation types, to preserve future back-compatibility."""

    model_config = ConfigDict(extra="allow")
    aggregation_type: None

    @field_validator("aggregation_type", mode="before")
    @classmethod
    def ensure_filter_type_unknown(cls, value: Any) -> None:
        if value in set(KnownAggregationType):
            raise ValueError(
                f"{value} is an known aggregation type, but validation failed, "
                "so the response was not as expected. "
                "Try upgrading the weaviate-agents package to a new version."
            )
        return None

    def model_post_init(self, context: Any) -> None:
        warnings.warn(
            f"The aggregation_type {self.aggregation_type} wasn't recognised. "
            "Try upgrading the weaviate-agents package to a new version."
        )


PropertyAggregation = Union[
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
    aggregations: list[PropertyAggregation]
    filters: list[PropertyFilter] = []


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
