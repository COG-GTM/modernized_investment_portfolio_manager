from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from schemas.esg import EsgClearOverrideRequest, EsgMetricResponse, EsgOverrideRequest
from services import esg_service
from services.esg_service import AccountNotFoundError, EsgStateError

router = APIRouter(prefix="/api", tags=["esg"])


def _handle(fn, *args):
    try:
        return fn(*args)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except EsgStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/portfolio/{account_number}/esg", response_model=EsgMetricResponse)
def get_esg(account_number: str, db: Session = Depends(get_db)):
    """Carbon intensity (WACI) for the portfolio's current as-of month."""
    return _handle(esg_service.get_esg_metric, db, account_number)


@router.put("/portfolio/{account_number}/esg/override", response_model=EsgMetricResponse)
def put_esg_override(account_number: str, body: EsgOverrideRequest, db: Session = Depends(get_db)):
    """Override the effective WACI for the current as-of month with a mandatory reason."""
    return _handle(esg_service.set_override, db, account_number, body.value, body.reason, body.changedBy)


@router.delete("/portfolio/{account_number}/esg/override", response_model=EsgMetricResponse)
def delete_esg_override(account_number: str, body: EsgClearOverrideRequest, db: Session = Depends(get_db)):
    """Clear the current month's override; a reason is still required."""
    return _handle(esg_service.clear_override, db, account_number, body.reason, body.changedBy)
