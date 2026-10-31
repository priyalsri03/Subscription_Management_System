"""
Discounts API - CRUD endpoints for Discount models
Person 2 can use these to display discount information.
Note: Discount CRUD operations can be used by both teams for usage tracking.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.app.core.db import get_db
from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.interfaces import User
from backend.app.models.discount import Discount
from backend.app.models.product import Product


router = APIRouter(prefix="/api/v1/discounts", tags=["discounts"])


class DiscountResponse(BaseModel):
    id: int
    name: str
    kind: str  # fixed or percent
    value: Decimal
    min_purchase: Optional[Decimal] = None
    min_quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = None
    times_used: int = 0
    applies_to: str  # product or subscription
    product_id: Optional[int] = None

    class Config:
        from_attributes = True


class DiscountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    kind: str = Field(..., pattern="^(fixed|percent)$")
    value: Decimal = Field(..., gt=0)
    min_purchase: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = Field(None, ge=1)
    applies_to: str = Field(..., pattern="^(product|subscription|both)$")
    product_id: Optional[int] = None


class DiscountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    kind: Optional[str] = Field(None, pattern="^(fixed|percent)$")
    value: Optional[Decimal] = Field(None, gt=0)
    min_purchase: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = Field(None, ge=1)
    applies_to: Optional[str] = Field(None, pattern="^(product|subscription|both)$")
    product_id: Optional[int] = None


@router.post("", response_model=DiscountResponse, status_code=201)
def create_discount(
    discount_data: DiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    """Create a new discount."""
    # Validate product exists if product_id is provided
    if discount_data.product_id:
        product = db.query(Product).filter(Product.id == discount_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

    discount = Discount(
        name=discount_data.name,
        kind=discount_data.kind,
        value=discount_data.value,
        min_purchase=discount_data.min_purchase,
        min_quantity=discount_data.min_quantity,
        start_date=discount_data.start_date,
        end_date=discount_data.end_date,
        usage_limit=discount_data.usage_limit,
        applies_to=discount_data.applies_to,
        product_id=discount_data.product_id,
    )
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return _build_discount_response(discount)


@router.patch("/{discount_id}", response_model=DiscountResponse)
def update_discount(
    discount_id: int,
    discount_data: DiscountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    """Update an existing discount."""
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")

    update_data = discount_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(discount, field, value)

    db.commit()
    db.refresh(discount)
    return _build_discount_response(discount)


@router.get("", response_model=List[DiscountResponse])
def list_discounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    applies_to: Optional[str] = Query(None, description="Filter by applies_to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all discounts, optionally filtered."""
    today = date.today()
    query = db.query(Discount)

    # Filter by active status (currently valid date range)
    if is_active is True:
        query = query.filter(
            (Discount.start_date.is_(None) | (Discount.start_date <= today)),
            (Discount.end_date.is_(None) | (Discount.end_date >= today)),
        )
    elif is_active is False:
        query = query.filter(
            Discount.end_date < today
        )

    if applies_to:
        query = query.filter(Discount.applies_to == applies_to)

    discounts = query.offset(skip).limit(limit).all()
    return [_build_discount_response(d) for d in discounts]


@router.get("/{discount_id}", response_model=DiscountResponse)
def get_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single discount."""
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    return _build_discount_response(discount)


@router.delete("/{discount_id}", status_code=204)
def delete_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    """Delete a discount."""
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")

    db.delete(discount)
    db.commit()


def _build_discount_response(discount: Discount) -> DiscountResponse:
    return DiscountResponse(
        id=discount.id,
        name=discount.name,
        kind=discount.kind,
        value=discount.value,
        min_purchase=discount.min_purchase,
        min_quantity=discount.min_quantity,
        start_date=discount.start_date,
        end_date=discount.end_date,
        usage_limit=discount.usage_limit,
        times_used=discount.times_used,
        applies_to=discount.applies_to,
        product_id=discount.product_id,
    )