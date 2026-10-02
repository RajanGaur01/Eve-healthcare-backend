from fastapi import FastAPI

app = FastAPI(
    title="EVE Healthcare Diagnostic Booking API",
    description=(
        "Backend service for diagnostic centre discovery, "
        "test bookings, and simulated payments."
    ),
    version="1.0.0",
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "message": "EVE Healthcare Diagnostic Booking API",
        "documentation": "/docs",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }
