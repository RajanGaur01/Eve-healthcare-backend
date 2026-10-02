from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import (
    CurrentUser,
    DatabaseSession,
)
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payments import (
    PaymentCreate,
    PaymentResponse,
    PaymentWebhook,
    WebhookResponse,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


def update_booking_from_payment(
    booking: Booking,
    payment_status: PaymentStatus,
) -> None:
    if payment_status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def simulate_payment(
    payload: PaymentCreate,
    database: DatabaseSession,
    current_user: CurrentUser,
) -> Payment:
    booking = database.scalar(
        select(Booking)
        .where(
            Booking.id == payload.booking_id,
            Booking.user_id == current_user.id,
        )
        .with_for_update()
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A cancelled booking cannot be paid",
        )

    if booking.status == BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This booking has already been paid",
        )

    if booking.status == BookingStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment has already failed for this booking",
        )

    payment = Payment(
        booking_id=booking.id,
        event_id=f"evt_{uuid4().hex}",
        provider_reference=f"pay_{uuid4().hex}",
        amount=booking.amount,
        status=payload.simulate,
    )

    update_booking_from_payment(
        booking,
        payload.simulate,
    )

    database.add(payment)

    try:
        database.commit()
        database.refresh(payment)
    except IntegrityError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate payment could not be processed",
        )

    return payment


@router.post(
    "/webhook",
    response_model=WebhookResponse,
)
def payment_webhook(
    payload: PaymentWebhook,
    database: DatabaseSession,
) -> WebhookResponse:
    existing_payment = database.scalar(
        select(Payment).where(
            Payment.event_id == payload.event_id
        )
    )

    if existing_payment is not None:
        return WebhookResponse(
            message="Webhook event already processed",
            duplicate=True,
            payment=existing_payment,
        )

    booking = database.scalar(
        select(Booking)
        .where(Booking.id == payload.booking_id)
        .with_for_update()
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if Decimal(booking.amount) != Decimal(payload.amount):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount does not match booking amount",
        )

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A cancelled booking cannot receive payment",
        )

    if booking.status == BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking is already confirmed",
        )

    payment = Payment(
        booking_id=booking.id,
        event_id=payload.event_id,
        provider_reference=payload.provider_reference,
        amount=payload.amount,
        status=payload.status,
    )

    update_booking_from_payment(
        booking,
        payload.status,
    )

    database.add(payment)

    try:
        database.commit()
        database.refresh(payment)

    except IntegrityError:
        database.rollback()

        existing_payment = database.scalar(
            select(Payment).where(
                Payment.event_id == payload.event_id
            )
        )

        if existing_payment is not None:
            return WebhookResponse(
                message="Webhook event already processed",
                duplicate=True,
                payment=existing_payment,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment event could not be processed",
        )

    return WebhookResponse(
        message="Webhook processed successfully",
        duplicate=False,
        payment=payment,
    )