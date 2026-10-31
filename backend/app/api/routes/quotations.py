"""
Quotation Template API - Person 2
Uses Person 1's services via interfaces.
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.db import get_db
from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.interfaces import (
    get_plan_repo, get_product_repo,
    User
)
from backend.app.models.quotation import QuotationTemplate, QuotationTemplateLine

router = APIRouter(prefix="/api/v1/quotation-templates", tags=["quotation-templates"])


class TemplateLineCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1)


class TemplateLineResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int]
    quantity: int
    product_name: str
    variant_value: Optional[str]

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    plan_id: int
    validity_days: int = Field(default=30, ge=1)
    lines: List[TemplateLineCreate] = []


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    plan_id: Optional[int] = None
    validity_days: Optional[int] = Field(None, ge=1)


class TemplateResponse(BaseModel):
    id: int
    name: str
    plan_id: int
    plan_name: str
    validity_days: int
    lines: List[TemplateLineResponse] = []

    class Config:
        from_attributes = True


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    plan = get_plan_repo().get_plan(db, template_data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    template = QuotationTemplate(
        name=template_data.name,
        plan_id=template_data.plan_id,
        validity_days=template_data.validity_days,
    )
    db.add(template)
    db.flush()

    for line_data in template_data.lines:
        product = get_product_repo().get_product(db, line_data.product_id)
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product {line_data.product_id} not found"
            )

        line = QuotationTemplateLine(
            template_id=template.id,
            product_id=line_data.product_id,
            variant_id=line_data.variant_id,
            quantity=line_data.quantity,
        )
        db.add(line)

    db.commit()
    db.refresh(template)
    return _build_template_response(template, db)


@router.get("", response_model=List[TemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    templates = db.query(QuotationTemplate).offset(skip).limit(limit).all()
    return [_build_template_response(t, db) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = (
        db.query(QuotationTemplate)
        .filter(QuotationTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _build_template_response(template, db)


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    template = (
        db.query(QuotationTemplate)
        .filter(QuotationTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = template_data.model_dump(exclude_unset=True)
    if "plan_id" in update_data:
        plan = get_plan_repo().get_plan(db, update_data["plan_id"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return _build_template_response(template, db)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    template = (
        db.query(QuotationTemplate)
        .filter(QuotationTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()


@router.post("/{template_id}/lines", response_model=TemplateLineResponse)
def add_template_line(
    template_id: int,
    line_data: TemplateLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    template = (
        db.query(QuotationTemplate)
        .filter(QuotationTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    product = get_product_repo().get_product(db, line_data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    line = QuotationTemplateLine(
        template_id=template_id,
        product_id=line_data.product_id,
        variant_id=line_data.variant_id,
        quantity=line_data.quantity,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return _build_line_response(line, db)


@router.delete("/lines/{line_id}", status_code=204)
def delete_template_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    line = (
        db.query(QuotationTemplateLine)
        .filter(QuotationTemplateLine.id == line_id)
        .first()
    )
    if not line:
        raise HTTPException(status_code=404, detail="Template line not found")
    db.delete(line)
    db.commit()


def _build_template_response(template: QuotationTemplate, db: Session) -> TemplateResponse:
    plan = get_plan_repo().get_plan(db, template.plan_id)
    lines = [
        _build_line_response(line, db) for line in template.lines
    ]
    return TemplateResponse(
        id=template.id,
        name=template.name,
        plan_id=template.plan_id,
        plan_name=plan.name if plan else "Unknown",
        validity_days=template.validity_days,
        lines=lines,
    )


def _build_line_response(line: QuotationTemplateLine, db: Session) -> TemplateLineResponse:
    product = get_product_repo().get_product(db, line.product_id)
    variant = None
    if line.variant_id:
        variant = get_product_repo().get_variant(db, line.variant_id)
    return TemplateLineResponse(
        id=line.id,
        product_id=line.product_id,
        variant_id=line.variant_id,
        quantity=line.quantity,
        product_name=product.name if product else "Unknown",
        variant_value=variant.value if variant else None,
    )