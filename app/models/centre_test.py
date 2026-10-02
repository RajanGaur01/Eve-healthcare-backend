from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.centre import DiagnosticCentre
    from app.models.diagnostic_test import DiagnosticTest


class CentreTest(Base):
    __tablename__ = "centre_tests"

    __table_args__ = (
        UniqueConstraint(
            "centre_id",
            "test_id",
            name="uq_centre_test",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    centre_id: Mapped[int] = mapped_column(
        ForeignKey(
            "diagnostic_centres.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    test_id: Mapped[int] = mapped_column(
        ForeignKey(
            "diagnostic_tests.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    centre: Mapped["DiagnosticCentre"] = relationship(
        back_populates="test_offerings",
    )

    diagnostic_test: Mapped["DiagnosticTest"] = relationship(
        back_populates="centre_offerings",
    )