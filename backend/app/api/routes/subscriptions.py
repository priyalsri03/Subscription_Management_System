"""
Subscription API - Person 2
Uses Person 1's services via interfaces.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta

from backend.app.core.db import get_db
from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.interfaces import (
    get_plan_repo, get_product_repo, get_pricing,
    User, Product
)
from backend.app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus
from backend.app.models.quotation import QuotationTemplate
from backend.app.models.user import User as UserModel
from backend.app.services.subscriptions import (
    create_subscription_from_template,
    transition_status,
    pause_subscription,
    resume_subscription,
    add_subscription_line,
)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


class SubscriptionLineCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1)
    tax_id: Optional[int] = None


class SubscriptionLineResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int]
    quantity: int
    unit_price: Decimal
    tax_id: Optional[int]
    amount: Decimal
    product_name: str
    variant_value: Optional[str]

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    template_id: Optional[int] = None
    customer_id: int
    plan_id: Optional[int] = None  # Required only if template_id not provided
    start_date: date
    payment_terms: Optional[str] = None
    lines: List[SubscriptionLineCreate] = []

    # Validation: either template_id or plan_id must be provided
    def validate_plan_source(self):
        if self.template_id is None and self.plan_id is None:
            raise ValueError("Either template_id or plan_id must be provided")
        if self.template_id is not None and self.plan_id is not None:
            raise ValueError("Provide only one of template_id or plan_id")
        return True


class SubscriptionUpdate(BaseModel):
    payment_terms: Optional[str] = None
    is_paused: Optional[bool] = None


class SubscriptionResponse(BaseModel):
    id: int
    number: str
    customer_id: int
    customer_name: str
    plan_id: int
    plan_name: str
    start_date: date
    expiry_date: date
    payment_terms: Optional[str]
    status: str
    is_paused: bool
    lines: List[SubscriptionLineResponse] = []

    class Config:
        from_attributes = True


class StatusTransition(BaseModel):
    new_status: str = Field(..., pattern="^(draft|quotation|confirmed|active|closed)$")


@router.post("", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    sub_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    # If template provided, create from template
    if sub_data.template_id:
        template = (
            db.query(QuotationTemplate)
            .filter(QuotationTemplate.id == sub_data.template_id)
            .first()
        )
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        count = db.query(Subscription).count() + 1
        sub_number = f"SUB-{count:06d}"

        sub = create_subscription_from_template(
            db=db,
            template_id=sub_data.template_id,
            customer_id=sub_data.customer_id,
            start_date=sub_data.start_date,
            subscription_number=sub_number,
        )
        return _build_subscription_response(sub, db)

    # Manual creation
    plan = get_plan_repo().get_plan(db, sub_data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Calculate expiry
    if plan.billing_period == "daily":
        expiry = sub_data.start_date + timedelta(days=1)
    elif plan.billing_period == "weekly":
        expiry = sub_data.start_date + timedelta(weeks=1)
    elif plan.billing_period == "monthly":
        expiry = sub_data.start_date + relativedelta(months=1)
    elif plan.billing_period == "yearly":
        expiry = sub_data.start_date + relativedelta(years=1)
    else:
        expiry = sub_data.start_date

    count = db.query(Subscription).count() + 1
    sub_number = f"SUB-{count:06d}"

    sub = Subscription(
        number=sub_number,
        customer_id=sub_data.customer_id,
        plan_id=plan.id,
        start_date=sub_data.start_date,
        expiry_date=expiry,
        payment_terms=sub_data.payment_terms,
        status=SubscriptionStatus.DRAFT,
    )
    db.add(sub)
    db.flush()

    for line_data in sub_data.lines:
        product = get_product_repo().get_product(db, line_data.product_id)
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product {line_data.product_id} not found"
            )

        price = get_pricing().unit_price(db, line_data.product_id, line_data.variant_id)

        line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=line_data.product_id,
            variant_id=line_data.variant_id,
            quantity=line_data.quantity,
            unit_price=price,
            tax_id=line_data.tax_id,
            amount=price * line_data.quantity,
        )
        db.add(line)

    db.commit()
    db.refresh(sub)
    return _build_subscription_response(sub, db)


@router.get("", response_model=List[SubscriptionResponse])
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
):
    query = db.query(Subscription)

    # Customer can only see their own subscriptions
    if current_user.role == "customer":
        query = query.filter(Subscription.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Subscription.customer_id == customer_id)

    if status_filter:
        query = query.filter(Subscription.status == status_filter)

    subs = query.offset(skip).limit(limit).all()
    return [_build_subscription_response(s, db) for s in subs]


@router.get("/{sub_id}", response_model=SubscriptionResponse)
def get_subscription(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Customer can only see their own
    if current_user.role == "customer" and sub.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your subscription")

    return _build_subscription_response(sub, db)


@router.patch("/{sub_id}", response_model=SubscriptionResponse)
def update_subscription(
    sub_id: int,
    sub_data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    update_data = sub_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sub, field, value)

    db.commit()
    db.refresh(sub)
    return _build_subscription_response(sub, db)


@router.post("/{sub_id}/status", response_model=SubscriptionResponse)
def change_status(
    sub_id: int,
    transition: StatusTransition,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    try:
        sub = transition_status(db, sub, transition.new_status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_subscription_response(sub, db)


@router.post("/{sub_id}/pause", response_model=SubscriptionResponse)
def pause(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    try:
        sub = pause_subscription(db, sub)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_subscription_response(sub, db)


@router.post("/{sub_id}/resume", response_model=SubscriptionResponse)
def resume(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    try:
        sub = resume_subscription(db, sub)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_subscription_response(sub, db)


@router.post("/{sub_id}/lines", response_model=SubscriptionLineResponse)
def add_line(
    sub_id: int,
    line_data: SubscriptionLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    try:
        line = add_subscription_line(
            db=db,
            sub=sub,
            product_id=line_data.product_id,
            quantity=line_data.quantity,
            variant_id=line_data.variant_id,
            tax_id=line_data.tax_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_line_response(line, db)


def _build_subscription_response(sub: Subscription, db: Session) -> SubscriptionResponse:
    customer = db.query(UserModel).filter(UserModel.id == sub.customer_id).first()
    plan = get_plan_repo().get_plan(db, sub.plan_id)
    lines = [
        _build_line_response(line, db) for line in sub.lines
    ]
    return SubscriptionResponse(
        id=sub.id,
        number=sub.number,
        customer_id=sub.customer_id,
        customer_name=customer.name if customer else "Unknown",
        plan_id=sub.plan_id,
        plan_name=plan.name if plan else "Unknown",
        start_date=sub.start_date,
        expiry_date=sub.expiry_date,
        payment_terms=sub.payment_terms,
        status=sub.status,
        is_paused=sub.is_paused,
        lines=lines,
    )


def _build_line_response(line: SubscriptionLine, db: Session) -> SubscriptionLineResponse:
    product = get_product_repo().get_product(db, line.product_id)
    variant = None
    if line.variant_id:
        variant = get_product_repo().get_variant(db, line.variant_id)
    return SubscriptionLineResponse(
        id=line.id,
        product_id=line.product_id,
        variant_id=line.variant_id,
        quantity=line.quantity,
        unit_price=line.unit_price,
        tax_id=line.tax_id,
        amount=line.amount,
        product_name=product.name if product else "Unknown",
        variant_value=variant.value if variant else None,
    )