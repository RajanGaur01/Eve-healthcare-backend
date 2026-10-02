from fastapi.testclient import TestClient


def create_user(
    client: TestClient,
    email: str = "rajan@example.com",
    password: str = "RajanPass123",
) -> dict:
    response = client.post(
        "/auth/signup",
        json={
            "name": "Rajan Kumar",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(
    client: TestClient,
    email: str = "rajan@example.com",
    password: str = "RajanPass123",
) -> str:
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def authorization_header(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_authenticated_user(
    client: TestClient,
    email: str = "rajan@example.com",
) -> dict[str, str]:
    create_user(client, email=email)
    token = login_user(client, email=email)

    return authorization_header(token)


def create_test_offering(
    client: TestClient,
    headers: dict[str, str],
    price: float = 599.00,
) -> int:
    centre_response = client.post(
        "/centres",
        headers=headers,
        json={
            "name": "EVE Diagnostics Ghaziabad",
            "location": "Raj Nagar, Ghaziabad",
        },
    )

    assert centre_response.status_code == 201
    centre_id = centre_response.json()["id"]

    test_response = client.post(
        "/tests",
        headers=headers,
        json={
            "name": "Complete Blood Count",
            "description": "Blood component analysis",
        },
    )

    assert test_response.status_code == 201
    test_id = test_response.json()["id"]

    offering_response = client.post(
        f"/centres/{centre_id}/tests",
        headers=headers,
        json={
            "test_id": test_id,
            "price": price,
        },
    )

    assert offering_response.status_code == 201

    return offering_response.json()["offering_id"]


def create_booking(
    client: TestClient,
    headers: dict[str, str],
    offering_id: int,
) -> dict:
    response = client.post(
        "/bookings",
        headers=headers,
        json={
            "centre_test_id": offering_id,
            "appointment_at": "2030-10-05T10:30:00+05:30",
        },
    )

    assert response.status_code == 201

    return response.json()