"""
Invoice API - Person 2
Uses Person 1's services via interfaces.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.db import get_db
from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.interfaces import User
from backend.app.models.invoice import Invoice, InvoiceLine
from backend.app.models.subscription import Subscription
from backend.app.models.product import Product as ProductModel
from backend.app.models.user import User as UserModel
from backend.app.services.billing import generate_invoice_for_subscription, run_billing_cycle
from backend.app.services.payments import get_outstanding_amount

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


class InvoiceLineResponse(BaseModel):
    id: int
    product_id: int
    description: Optional[str]
    quantity: int
    unit_price: Decimal
    tax_amount: Decimal
    amount: Decimal
    product_name: str

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: int
    number: str
    subscription_id: int
    subscription_number: str
    customer_id: int
    customer_name: str
    period_start: date
    period_end: date
    issue_date: date
    due_date: date
    status: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    subscription_id: int
    period_start: date
    period_end: date
    issue_date: Optional[date] = None
    due_date: Optional[date] = None


@router.post("", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    try:
        invoice = generate_invoice_for_subscription(
            db=db,
            subscription_id=invoice_data.subscription_id,
            period_start=invoice_data.period_start,
            period_end=invoice_data.period_end,
            issue_date=invoice_data.issue_date,
            due_date=invoice_data.due_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_invoice_response(invoice, db)


@router.post("/billing-cycle", response_model=List[InvoiceResponse])
def trigger_billing_cycle(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    """Run the billing cycle for a specific date (or today)."""
    invoices = run_billing_cycle(db, as_of_date)
    return [_build_invoice_response(inv, db) for inv in invoices]


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    subscription_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
):
    query = db.query(Invoice)

    # Customer can only see their own invoices
    if current_user.role == "customer":
        query = query.filter(Invoice.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if subscription_id:
        query = query.filter(Invoice.subscription_id == subscription_id)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    invoices = query.order_by(Invoice.issue_date.desc()).offset(skip).limit(limit).all()
    return [_build_invoice_response(inv, db) for inv in invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Customer can only see their own
    if current_user.role == "customer" and invoice.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your invoice")

    return _build_invoice_response(invoice, db)


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be confirmed")

    invoice.status = "confirmed"
    db.commit()
    db.refresh(invoice)
    return _build_invoice_response(invoice, db)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status not in ["draft", "confirmed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel paid or already cancelled invoice")

    invoice.status = "cancelled"
    db.commit()
    db.refresh(invoice)
    return _build_invoice_response(invoice, db)


@router.get("/{invoice_id}/outstanding", response_model=dict)
def get_outstanding(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get outstanding amount for an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Customer can only see their own invoices
    if current_user.role == "customer" and invoice.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your invoice")

    outstanding = get_outstanding_amount(db, invoice_id)
    return {"outstanding": outstanding}


def _build_invoice_response(invoice: Invoice, db: Session) -> InvoiceResponse:
    subscription = db.query(Subscription).filter(Subscription.id == invoice.subscription_id).first()
    customer = db.query(UserModel).filter(UserModel.id == invoice.customer_id).first()
    lines = [
        _build_line_response(line, db) for line in invoice.lines
    ]
    return InvoiceResponse(
        id=invoice.id,
        number=invoice.number,
        subscription_id=invoice.subscription_id,
        subscription_number=subscription.number if subscription else "Unknown",
        customer_id=invoice.customer_id,
        customer_name=customer.name if customer else "Unknown",
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        status=invoice.status,
        subtotal=invoice.subtotal,
        discount_total=invoice.discount_total,
        tax_total=invoice.tax_total,
        total=invoice.total,
        amount_paid=invoice.amount_paid,
        lines=lines,
    )


def _build_line_response(line: InvoiceLine, db: Session) -> InvoiceLineResponse:
    product = db.query(ProductModel).filter(ProductModel.id == line.product_id).first()
    return InvoiceLineResponse(
        id=line.id,
        product_id=line.product_id,
        description=line.description,
        quantity=line.quantity,
        unit_price=line.unit_price,
        tax_amount=line.tax_amount,
        amount=line.amount,
        product_name=product.name if product else "Unknown",
    )