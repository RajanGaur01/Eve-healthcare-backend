# EVE Healthcare Diagnostic Booking API

A backend service for managing diagnostic centres, diagnostic tests, patient bookings, and simulated payment processing.

This project was developed as part of the EVE Healthcare SDE Intern backend engineering assignment.

## Features

- User signup and login
- JWT-based authentication
- Secure password hashing using Argon2
- Diagnostic centre management
- Diagnostic test management
- Centre-specific test pricing
- Authenticated diagnostic test bookings
- User-specific booking access
- Booking cancellation
- Simulated payment processing
- Idempotent payment webhook
- Database-level protection against duplicate webhook events
- Input validation and structured error responses
- Alembic database migrations
- Automated API and integration tests

## Technology Stack

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Pydantic
- PyJWT
- pwdlib with Argon2
- Psycopg 3
- Pytest
- HTTPX

## Project Structure

```text
.
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── models/
│   │   ├── booking.py
│   │   ├── centre.py
│   │   ├── centre_test.py
│   │   ├── diagnostic_test.py
│   │   ├── payment.py
│   │   └── user.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── bookings.py
│   │   ├── centres.py
│   │   └── payments.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── bookings.py
│   │   ├── centres.py
│   │   └── payments.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_auth.py
│   ├── test_bookings.py
│   └── test_payments.py
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## Database Design

### Users

Stores registered users and their password hashes.

```text
users
├── id
├── name
├── email
├── password_hash
└── created_at
```

The email column is unique.

### Diagnostic Centres

Stores information about diagnostic centres.

```text
diagnostic_centres
├── id
├── name
├── location
└── created_at
```

### Diagnostic Tests

Stores reusable diagnostic test definitions.

```text
diagnostic_tests
├── id
├── name
├── description
└── created_at
```

### Centre Test Offerings

Connects diagnostic centres with tests and stores centre-specific pricing.

```text
centre_tests
├── id
├── centre_id
├── test_id
├── price
└── is_available
```

The combination of `centre_id` and `test_id` is unique.

### Bookings

Stores diagnostic test appointments created by authenticated users.

```text
bookings
├── id
├── user_id
├── centre_test_id
├── appointment_at
├── amount
├── status
├── created_at
└── updated_at
```

Booking statuses:

- `PENDING`
- `CONFIRMED`
- `FAILED`
- `CANCELLED`

### Payments

Stores simulated payment results and webhook events.

```text
payments
├── id
├── booking_id
├── event_id
├── provider_reference
├── amount
├── status
└── created_at
```

Payment statuses:

- `SUCCESS`
- `FAILED`

The `event_id` column is unique to provide database-level webhook idempotency.

## Local Setup

### Prerequisites

Install:

- Python 3.13 or a compatible Python 3 version
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd eve-healthcare-backend
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the PostgreSQL database

Open PostgreSQL and run:

```sql
CREATE DATABASE eve_healthcare;
```

### 5. Configure environment variables

Copy `.env.example` to `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux or macOS:

```bash
cp .env.example .env
```

Update `.env` with your PostgreSQL credentials:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/eve_healthcare
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Never commit the `.env` file.

### 6. Apply database migrations

```bash
python -m alembic upgrade head
```

### 7. Start the API

```bash
uvicorn app.main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

Health check:

```text
http://127.0.0.1:8000/health
```

## API Endpoints

### Authentication

```text
POST /auth/signup
POST /auth/login
GET  /auth/me
```

### Diagnostic Centres and Tests

```text
POST /centres
GET  /centres
GET  /centres/{centre_id}

POST /tests
GET  /tests

POST /centres/{centre_id}/tests
```

### Bookings

```text
POST  /bookings
GET   /bookings
GET   /bookings/{booking_id}
PATCH /bookings/{booking_id}/cancel
```

### Payments

```text
POST /payments
POST /payments/webhook
```

## Example API Requests

### User Signup

```http
POST /auth/signup
Content-Type: application/json
```

```json
{
  "name": "Rajan Kumar",
  "email": "rajan@example.com",
  "password": "RajanPass123"
}
```

### User Login

The login endpoint accepts form data.

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded
```

```text
username=rajan@example.com
password=RajanPass123
```

Example response:

```json
{
  "access_token": "JWT_ACCESS_TOKEN",
  "token_type": "bearer"
}
```

Protected endpoints require:

```http
Authorization: Bearer JWT_ACCESS_TOKEN
```

### Create a Diagnostic Centre

```json
{
  "name": "EVE Diagnostics Ghaziabad",
  "location": "Raj Nagar, Ghaziabad"
}
```

### Create a Diagnostic Test

```json
{
  "name": "Complete Blood Count",
  "description": "Measures different components of blood."
}
```

### Add a Test to a Centre

```json
{
  "test_id": 1,
  "price": 599.00
}
```

### Create a Booking

```json
{
  "centre_test_id": 1,
  "appointment_at": "2030-10-05T10:30:00+05:30"
}
```

The booking amount is obtained from the centre-test offering stored in the database. Clients cannot submit or modify the booking amount.

### Simulate a Successful Payment

```json
{
  "booking_id": 1,
  "simulate": "SUCCESS"
}
```

A successful payment changes the booking status from `PENDING` to `CONFIRMED`.

### Simulate a Failed Payment

```json
{
  "booking_id": 1,
  "simulate": "FAILED"
}
```

A failed payment changes the booking status from `PENDING` to `FAILED`.

### Payment Webhook

```json
{
  "event_id": "evt_example_001",
  "booking_id": 1,
  "provider_reference": "pay_example_001",
  "status": "SUCCESS",
  "amount": 599.00
}
```

## Webhook Idempotency

Payment providers may send the same webhook event multiple times. The webhook implementation prevents duplicate processing through two layers:

1. The application checks whether the supplied `event_id` already exists.
2. The database enforces a unique constraint on `payments.event_id`.

If an event has already been processed, the API returns the existing payment with:

```json
{
  "message": "Webhook event already processed",
  "duplicate": true
}
```

The duplicate event does not create another payment or modify the confirmed booking again.

The booking row is locked during payment processing to reduce the risk of concurrent payment requests processing the same pending booking.

## Booking and Payment Rules

- Users can access only their own bookings.
- Booking amounts are copied from the database.
- Clients cannot provide booking prices.
- Appointment dates must be in the future.
- Appointment timestamps must include timezone information.
- New bookings begin with `PENDING` status.
- Only pending bookings can be cancelled.
- Cancelled bookings cannot be paid.
- Confirmed bookings cannot be paid again.
- Successful payments confirm bookings.
- Failed payments mark bookings as failed.
- Webhook amounts must match booking amounts.
- Duplicate webhook events return the existing payment.

## Running Tests

### 1. Create a separate test database

```sql
CREATE DATABASE eve_healthcare_test;
```

### 2. Configure the test database

Update the test database URL in `tests/conftest.py` with your local PostgreSQL credentials.

The database name must remain:

```text
eve_healthcare_test
```

Do not point the tests at the development database because test setup recreates database tables.

### 3. Run the complete test suite

```bash
python -m pytest -v
```

The test suite covers:

- Successful signup
- Duplicate email rejection
- Successful login
- Invalid login
- Protected endpoint authentication
- Database-controlled booking pricing
- Past appointment rejection
- Booking ownership protection
- Booking cancellation
- Successful payment handling
- Failed payment handling
- Payment amount validation
- Invalid resource handling
- Duplicate webhook idempotency

## Important Assumptions

- Users may access and modify only their own bookings.
- Diagnostic centre and test creation endpoints represent administrative operations.
- Formal role-based access control is outside the assignment scope.
- The backend is the source of truth for diagnostic test prices.
- Appointment timestamps are converted to UTC before storage.
- A booking can have only one final payment outcome in the current implementation.
- Failed bookings require a new booking rather than a payment retry.
- Real payment gateway integration is outside the assignment scope.
- The simulated webhook does not use payment-provider signature verification.
- PostgreSQL is used as the primary database.

## Security Considerations

- Passwords are hashed using Argon2.
- Plaintext passwords are never stored.
- JWT tokens have expiration times.
- Protected resources require bearer authentication.
- Users cannot retrieve or cancel another user's booking.
- Database credentials and JWT secrets are loaded from environment variables.
- Payment amounts are validated against booking amounts.
- Unique database constraints protect against duplicate webhook events.

## Known Limitations

- Administrative role management is not implemented.
- The webhook does not verify an HMAC or provider signature.
- Payment retries are not implemented for failed bookings.
- Pagination is not implemented.
- Rate limiting is not implemented.
- Docker configuration is not included.
- The project does not integrate with a real payment provider.
- Notification services are not implemented.

## Future Improvements

- Add role-based authorization for administrative endpoints.
- Add Docker and Docker Compose for consistent local environments.
- Add HMAC-based webhook signature verification.
- Add payment retry handling with explicit state-transition rules.
- Add pagination to centre, test, booking, and payment endpoints.
- Add API rate limiting.
- Add structured application logging.
- Add request correlation IDs.
- Add Redis caching where it provides measurable value.
- Add application monitoring and error reporting.
- Add CI automation to run tests on every pull request.
- Add additional concurrent webhook integration tests.

## Engineering Decisions

### Why FastAPI?

FastAPI provides request validation, dependency injection, type-driven development, and OpenAPI documentation with minimal boilerplate.

### Why PostgreSQL?

PostgreSQL provides transactions, row-level locking, relational constraints, and reliable uniqueness enforcement required by the payment workflow.

### Why a Centre-Test Association Table?

The same diagnostic test may be offered by multiple centres at different prices. The `centre_tests` table models that relationship without duplicating test definitions.

### Why Decimal Prices?

Financial values use fixed-precision decimal database columns instead of floating-point values to prevent precision errors.

### Why Database-Level Idempotency?

An application-level existence check is vulnerable to simultaneous requests. A unique constraint on `event_id` ensures PostgreSQL rejects duplicate events even during a race condition.

## License

This project was created for the EVE Healthcare SDE Intern hiring assignment.