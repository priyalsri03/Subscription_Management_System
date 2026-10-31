"""
Plans API - Read-only endpoints for Plan models
Person 2 can use these to display plan information.
Note: Plan CRUD operations belong to Person 1.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.app.core.db import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.core.interfaces import User
from backend.app.models.plan import Plan

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


class PlanResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    billing_period: str
    min_quantity: int
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close: bool
    allow_early_close: bool
    allow_pause: bool
    allow_renew: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[PlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False, description="Only show active plans"),
):
    """List all plans."""
    query = db.query(Plan)

    if active_only:
        today = date.today()
        query = query.filter(
            (Plan.available_from.is_(None) | (Plan.available_from <= today)),
            (Plan.available_to.is_(None) | (Plan.available_to >= today)),
        )

    plans = query.offset(skip).limit(limit).all()
    return plans


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single plan."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Plan not found")

    return PlanResponse(
        id=plan.id,
        name=plan.name,
        price=plan.price,
        billing_period=plan.billing_period,
        min_quantity=plan.min_quantity,
        available_from=plan.available_from,
        available_to=plan.available_to,
        auto_close=plan.auto_close,
        allow_early_close=plan.allow_early_close,
        allow_pause=plan.allow_pause,
        allow_renew=plan.allow_renew
    )