from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CentreCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    location: str = Field(
        min_length=2,
        max_length=255,
    )


class CentreResponse(BaseModel):
    id: int
    name: str
    location: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiagnosticTestCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class DiagnosticTestResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CentreTestCreate(BaseModel):
    test_id: int = Field(gt=0)

    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )


class TestOfferingResponse(BaseModel):
    offering_id: int
    test_id: int
    test_name: str
    description: str | None
    price: Decimal
    is_available: bool


class CentreDetailResponse(CentreResponse):
    available_tests: list[TestOfferingResponse]