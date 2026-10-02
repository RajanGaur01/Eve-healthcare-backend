from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: int = Field(gt=0)
    simulate: PaymentStatus


class PaymentWebhook(BaseModel):
    event_id: str = Field(
        min_length=3,
        max_length=100,
    )

    booking_id: int = Field(gt=0)

    provider_reference: str = Field(
        min_length=3,
        max_length=100,
    )

    status: PaymentStatus

    amount: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    event_id: str
    provider_reference: str
    amount: Decimal
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookResponse(BaseModel):
    message: str
    duplicate: bool
    payment: PaymentResponse