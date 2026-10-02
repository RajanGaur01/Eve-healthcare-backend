from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.dependencies import CurrentUser, DatabaseSession
from app.models.booking import Booking, BookingStatus
from app.models.centre_test import CentreTest
from app.schemas.bookings import (
    BookingCreate,
    BookingDetailResponse,
    BookingResponse,
)


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


def build_booking_detail(
    booking: Booking,
) -> BookingDetailResponse:
    offering = booking.centre_test

    return BookingDetailResponse(
        id=booking.id,
        user_id=booking.user_id,
        centre_test_id=booking.centre_test_id,
        appointment_at=booking.appointment_at,
        amount=booking.amount,
        status=booking.status,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        centre_name=offering.centre.name,
        centre_location=offering.centre.location,
        test_name=offering.diagnostic_test.name,
    )


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    payload: BookingCreate,
    database: DatabaseSession,
    current_user: CurrentUser,
) -> Booking:
    appointment_utc = payload.appointment_at.astimezone(
        timezone.utc
    )

    if appointment_utc <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Appointment date and time must be in the future",
        )

    offering = database.get(
        CentreTest,
        payload.centre_test_id,
    )

    if offering is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centre test offering not found",
        )

    if not offering.is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This diagnostic test is currently unavailable",
        )

    booking = Booking(
        user_id=current_user.id,
        centre_test_id=offering.id,
        appointment_at=appointment_utc,
        amount=offering.price,
        status=BookingStatus.PENDING,
    )

    database.add(booking)
    database.commit()
    database.refresh(booking)

    return booking


@router.get(
    "",
    response_model=list[BookingResponse],
)
def list_my_bookings(
    database: DatabaseSession,
    current_user: CurrentUser,
) -> list[Booking]:
    bookings = database.scalars(
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
    ).all()

    return list(bookings)


@router.get(
    "/{booking_id}",
    response_model=BookingDetailResponse,
)
def get_booking(
    booking_id: int,
    database: DatabaseSession,
    current_user: CurrentUser,
) -> BookingDetailResponse:
    booking = database.scalar(
        select(Booking)
        .options(
            joinedload(Booking.centre_test).joinedload(
                CentreTest.centre
            ),
            joinedload(Booking.centre_test).joinedload(
                CentreTest.diagnostic_test
            ),
        )
        .where(
            Booking.id == booking_id,
            Booking.user_id == current_user.id,
        )
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return build_booking_detail(booking)


@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
)
def cancel_booking(
    booking_id: int,
    database: DatabaseSession,
    current_user: CurrentUser,
) -> Booking:
    booking = database.scalar(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == current_user.id,
        )
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status == BookingStatus.CANCELLED:
        return booking

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only pending bookings can be cancelled"
            ),
        )

    booking.status = BookingStatus.CANCELLED

    database.commit()
    database.refresh(booking)

    return booking