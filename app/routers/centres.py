from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, DatabaseSession
from app.models.centre import DiagnosticCentre
from app.models.centre_test import CentreTest
from app.models.diagnostic_test import DiagnosticTest
from app.schemas.centres import (
    CentreCreate,
    CentreDetailResponse,
    CentreResponse,
    CentreTestCreate,
    DiagnosticTestCreate,
    DiagnosticTestResponse,
    TestOfferingResponse,
)


router = APIRouter(
    tags=["Diagnostic Centres and Tests"],
)


@router.post(
    "/centres",
    response_model=CentreResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_centre(
    payload: CentreCreate,
    database: DatabaseSession,
    current_user: CurrentUser,
) -> DiagnosticCentre:
    centre = DiagnosticCentre(
        name=payload.name.strip(),
        location=payload.location.strip(),
    )

    database.add(centre)
    database.commit()
    database.refresh(centre)

    return centre


@router.get(
    "/centres",
    response_model=list[CentreResponse],
)
def list_centres(
    database: DatabaseSession,
) -> list[DiagnosticCentre]:
    centres = database.scalars(
        select(DiagnosticCentre).order_by(
            DiagnosticCentre.name
        )
    ).all()

    return list(centres)


@router.post(
    "/tests",
    response_model=DiagnosticTestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_diagnostic_test(
    payload: DiagnosticTestCreate,
    database: DatabaseSession,
    current_user: CurrentUser,
) -> DiagnosticTest:
    normalized_name = payload.name.strip()

    existing_test = database.scalar(
        select(DiagnosticTest).where(
            DiagnosticTest.name == normalized_name
        )
    )

    if existing_test is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A diagnostic test with this name already exists",
        )

    diagnostic_test = DiagnosticTest(
        name=normalized_name,
        description=(
            payload.description.strip()
            if payload.description
            else None
        ),
    )

    database.add(diagnostic_test)
    database.commit()
    database.refresh(diagnostic_test)

    return diagnostic_test


@router.get(
    "/tests",
    response_model=list[DiagnosticTestResponse],
)
def list_diagnostic_tests(
    database: DatabaseSession,
) -> list[DiagnosticTest]:
    tests = database.scalars(
        select(DiagnosticTest).order_by(
            DiagnosticTest.name
        )
    ).all()

    return list(tests)


@router.post(
    "/centres/{centre_id}/tests",
    response_model=TestOfferingResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_test_to_centre(
    centre_id: int,
    payload: CentreTestCreate,
    database: DatabaseSession,
    current_user: CurrentUser,
) -> TestOfferingResponse:
    centre = database.get(
        DiagnosticCentre,
        centre_id,
    )

    if centre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    diagnostic_test = database.get(
        DiagnosticTest,
        payload.test_id,
    )

    if diagnostic_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found",
        )

    existing_offering = database.scalar(
        select(CentreTest).where(
            CentreTest.centre_id == centre_id,
            CentreTest.test_id == payload.test_id,
        )
    )

    if existing_offering is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This test is already offered by the centre",
        )

    offering = CentreTest(
        centre_id=centre_id,
        test_id=payload.test_id,
        price=payload.price,
        is_available=True,
    )

    database.add(offering)
    database.commit()
    database.refresh(offering)

    return TestOfferingResponse(
        offering_id=offering.id,
        test_id=diagnostic_test.id,
        test_name=diagnostic_test.name,
        description=diagnostic_test.description,
        price=offering.price,
        is_available=offering.is_available,
    )


@router.get(
    "/centres/{centre_id}",
    response_model=CentreDetailResponse,
)
def get_centre(
    centre_id: int,
    database: DatabaseSession,
) -> CentreDetailResponse:
    centre = database.scalar(
        select(DiagnosticCentre)
        .options(
            selectinload(
                DiagnosticCentre.test_offerings
            ).selectinload(
                CentreTest.diagnostic_test
            )
        )
        .where(DiagnosticCentre.id == centre_id)
    )

    if centre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    available_tests = [
        TestOfferingResponse(
            offering_id=offering.id,
            test_id=offering.diagnostic_test.id,
            test_name=offering.diagnostic_test.name,
            description=offering.diagnostic_test.description,
            price=offering.price,
            is_available=offering.is_available,
        )
        for offering in centre.test_offerings
        if offering.is_available
    ]

    return CentreDetailResponse(
        id=centre.id,
        name=centre.name,
        location=centre.location,
        created_at=centre.created_at,
        available_tests=available_tests,
    )