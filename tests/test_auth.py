def test_signup_success(client):
    response = client.post(
        "/auth/signup",
        json={
            "name": "Rajan Kumar",
            "email": "rajan@example.com",
            "password": "RajanPass123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "rajan@example.com"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_duplicate_signup_returns_conflict(client):
    payload = {
        "name": "Rajan Kumar",
        "email": "rajan@example.com",
        "password": "RajanPass123",
    }

    first_response = client.post(
        "/auth/signup",
        json=payload,
    )

    second_response = client.post(
        "/auth/signup",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_success(client):
    client.post(
        "/auth/signup",
        json={
            "name": "Rajan Kumar",
            "email": "rajan@example.com",
            "password": "RajanPass123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "rajan@example.com",
            "password": "RajanPass123",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_wrong_password(client):
    client.post(
        "/auth/signup",
        json={
            "name": "Rajan Kumar",
            "email": "rajan@example.com",
            "password": "RajanPass123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "rajan@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_profile_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401