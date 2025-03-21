from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from weaviate.collections.classes.config import DataType


class OperationType(str, Enum):
    """Types of operations that can be performed on properties."""

    APPEND = "append"
    UPDATE = "update"


class OperationStep(BaseModel):
    """Base model for a transformation operation step."""

    property_name: str
    view_properties: List[str]
    instruction: str
    operation_type: OperationType


class AppendPropertyOperation(OperationStep):
    """Operation to append a new property."""

    data_type: DataType
    operation_type: OperationType = OperationType.APPEND


class UpdatePropertyOperation(OperationStep):
    """Operation to update an existing property."""

    operation_type: OperationType = OperationType.UPDATE


class DependentOperationStep(BaseModel):
    """A wrapper for operation steps that have dependencies on other operations."""

    operation: OperationStep
    depends_on: Optional[List[OperationStep]] = None

    def __init__(
        self, operation: OperationStep, depends_on: Optional[List[OperationStep]] = None
    ) -> None:
        super().__init__(operation=operation, depends_on=depends_on or [])


class TransformationResponse(BaseModel):
    """Response from a transformation operation."""

    workflow_id: str


class Operations:
    """Factory class for creating transformation operations."""

    @staticmethod
    def append_property(
        property_name: str,
        data_type: DataType,
        view_properties: List[str],
        instruction: str,
    ) -> AppendPropertyOperation:
        """Create an operation to append a new property.

        Args:
            property_name: Name of the new property to append
            data_type: Data type of the new property
            view_properties: List of property names to use as context for the transformation
            instruction: Instruction for how to generate the new property value

        Returns:
            An AppendPropertyOperation object
        """
        return AppendPropertyOperation(
            property_name=property_name,
            data_type=data_type,
            view_properties=view_properties,
            instruction=instruction,
        )

    @staticmethod
    def update_property(
        property_name: str,
        view_properties: List[str],
        instruction: str,
    ) -> UpdatePropertyOperation:
        """Create an operation to update an existing property.

        Args:
            property_name: Name of the property to update
            view_properties: List of property names to use as context for the transformation
            instruction: Instruction for how to update the property value

        Returns:
            An UpdatePropertyOperation object
        """
        return UpdatePropertyOperation(
            property_name=property_name,
            view_properties=view_properties,
            instruction=instruction,
        )
