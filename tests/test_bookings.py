from tests.helpers import (
    create_authenticated_user,
    create_booking,
    create_test_offering,
)


def test_booking_requires_authentication(client):
    response = client.post(
        "/bookings",
        json={
            "centre_test_id": 1,
            "appointment_at": "2030-10-05T10:30:00+05:30",
        },
    )

    assert response.status_code == 401


def test_booking_uses_database_price(client):
    headers = create_authenticated_user(client)

    offering_id = create_test_offering(
        client,
        headers,
        price=799.00,
    )

    booking = create_booking(
        client,
        headers,
        offering_id,
    )

    assert booking["amount"] == "799.00"
    assert booking["status"] == "PENDING"


def test_past_appointment_is_rejected(client):
    headers = create_authenticated_user(client)
    offering_id = create_test_offering(client, headers)

    response = client.post(
        "/bookings",
        headers=headers,
        json={
            "centre_test_id": offering_id,
            "appointment_at": "2020-01-01T10:30:00+05:30",
        },
    )

    assert response.status_code == 422


def test_user_cannot_access_another_users_booking(client):
    first_headers = create_authenticated_user(
        client,
        email="first@example.com",
    )

    offering_id = create_test_offering(
        client,
        first_headers,
    )

    booking = create_booking(
        client,
        first_headers,
        offering_id,
    )

    second_headers = create_authenticated_user(
        client,
        email="second@example.com",
    )

    response = client.get(
        f"/bookings/{booking['id']}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_pending_booking_can_be_cancelled(client):
    headers = create_authenticated_user(client)
    offering_id = create_test_offering(client, headers)

    booking = create_booking(
        client,
        headers,
        offering_id,
    )

    response = client.patch(
        f"/bookings/{booking['id']}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"