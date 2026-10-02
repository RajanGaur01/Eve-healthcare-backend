from fastapi import FastAPI
from app.routers.centres import router as centres_router
from app.routers.auth import router as auth_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router


app = FastAPI(
    title="EVE Healthcare Diagnostic Booking API",
    description=(
        "Backend service for diagnostic centre discovery, "
        "test bookings, and simulated payments."
    ),
    version="1.0.0",
)

app.include_router(bookings_router)
app.include_router(centres_router)
app.include_router(auth_router)
app.include_router(payments_router)


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