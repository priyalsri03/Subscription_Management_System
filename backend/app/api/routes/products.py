"""
Products API - Read-only endpoints for Product models
Person 2 can use these to display product information.
Note: Product CRUD operations belong to Person 1.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.app.core.db import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.core.interfaces import User
from backend.app.models.product import Product, ProductVariant

router = APIRouter(prefix="/api/v1/products", tags=["products"])


class ProductResponse(BaseModel):
    id: int
    name: str
    type: str
    sales_price: Decimal
    cost_price: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class VariantResponse(BaseModel):
    id: int
    product_id: int
    attribute: str
    value: str
    extra_price: Decimal

    class Config:
        from_attributes = True


class ProductDetailResponse(BaseModel):
    id: int
    name: str
    type: str
    sales_price: Decimal
    cost_price: Decimal
    notes: Optional[str] = None
    variants: List[VariantResponse] = []

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all products."""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.get("/search", response_model=List[ProductResponse])
def search_products(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search products by name."""
    products = (
        db.query(Product)
        .filter(Product.name.ilike(f"%{q}%"))
        .limit(100)
        .all()
    )
    return products


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single product with variants."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")

    variants = db.query(ProductVariant).filter(ProductVariant.product_id == product_id).all()

    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        type=product.type,
        sales_price=product.sales_price,
        cost_price=product.cost_price,
        notes=product.notes,
        variants=[
            VariantResponse(
                id=v.id,
                product_id=v.product_id,
                attribute=v.attribute,
                value=v.value,
                extra_price=v.extra_price
            )
            for v in variants
        ]
    )