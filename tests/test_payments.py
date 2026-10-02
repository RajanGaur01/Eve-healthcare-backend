from sqlalchemy import func, select

from app.models.payment import Payment
from tests.helpers import (
    create_authenticated_user,
    create_booking,
    create_test_offering,
)


def test_successful_payment_confirms_booking(client):
    headers = create_authenticated_user(client)
    offering_id = create_test_offering(client, headers)

    booking = create_booking(
        client,
        headers,
        offering_id,
    )

    payment_response = client.post(
        "/payments",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "simulate": "SUCCESS",
        },
    )

    assert payment_response.status_code == 201
    assert payment_response.json()["status"] == "SUCCESS"

    booking_response = client.get(
        f"/bookings/{booking['id']}",
        headers=headers,
    )

    assert booking_response.json()["status"] == "CONFIRMED"


def test_failed_payment_marks_booking_failed(client):
    headers = create_authenticated_user(client)
    offering_id = create_test_offering(client, headers)

    booking = create_booking(
        client,
        headers,
        offering_id,
    )

    response = client.post(
        "/payments",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "simulate": "FAILED",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "FAILED"

    booking_response = client.get(
        f"/bookings/{booking['id']}",
        headers=headers,
    )

    assert booking_response.json()["status"] == "FAILED"


def test_payment_amount_mismatch_is_rejected(client):
    headers = create_authenticated_user(client)

    offering_id = create_test_offering(
        client,
        headers,
        price=599.00,
    )

    booking = create_booking(
        client,
        headers,
        offering_id,
    )

    response = client.post(
        "/payments/webhook",
        json={
            "event_id": "evt_wrong_amount",
            "booking_id": booking["id"],
            "provider_reference": "pay_wrong_amount",
            "status": "SUCCESS",
            "amount": 100.00,
        },
    )

    assert response.status_code == 400


def test_duplicate_webhook_is_idempotent(
    client,
    database,
):
    headers = create_authenticated_user(client)
    offering_id = create_test_offering(client, headers)

    booking = create_booking(
        client,
        headers,
        offering_id,
    )

    payload = {
        "event_id": "evt_duplicate_001",
        "booking_id": booking["id"],
        "provider_reference": "pay_duplicate_001",
        "status": "SUCCESS",
        "amount": 599.00,
    }

    first_response = client.post(
        "/payments/webhook",
        json=payload,
    )

    second_response = client.post(
        "/payments/webhook",
        json=payload,
    )

    assert first_response.status_code == 200
    assert first_response.json()["duplicate"] is False

    assert second_response.status_code == 200
    assert second_response.json()["duplicate"] is True

    payment_count = database.scalar(
        select(func.count(Payment.id)).where(
            Payment.event_id == "evt_duplicate_001"
        )
    )

    assert payment_count == 1