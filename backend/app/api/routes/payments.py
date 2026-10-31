"""
Payment API - Person 2
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
from backend.app.models.payment import Payment
from backend.app.models.invoice import Invoice
from backend.app.services.payments import record_payment, get_invoice_payments, get_outstanding_amount

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal = Field(..., gt=0)
    method: str = Field(..., min_length=1, max_length=50)
    paid_on: Optional[date] = None
    note: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    invoice_number: str
    method: str
    amount: Decimal
    paid_on: date
    note: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "staff")),
):
    try:
        payment = record_payment(
            db=db,
            invoice_id=payment_data.invoice_id,
            amount=payment_data.amount,
            method=payment_data.method,
            paid_on=payment_data.paid_on,
            note=payment_data.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_payment_response(payment, db)


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    invoice_id: Optional[int] = Query(None),
):
    query = db.query(Payment)

    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)

    # Customer can only see payments on their invoices
    if current_user.role == "customer":
        invoice_ids = (
            db.query(Invoice.id)
            .filter(Invoice.customer_id == current_user.id)
            .all()
        )
        invoice_ids = [i[0] for i in invoice_ids]
        query = query.filter(Payment.invoice_id.in_(invoice_ids))

    payments = query.order_by(Payment.paid_on.desc()).offset(skip).limit(limit).all()
    return [_build_payment_response(p, db) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check ownership
    if current_user.role == "customer":
        invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
        if invoice and invoice.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your payment")

    return _build_payment_response(payment, db)


@router.get("/invoice/{invoice_id}/outstanding", response_model=dict)
def get_invoice_outstanding(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if current_user.role == "customer" and invoice.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your invoice")

    outstanding = get_outstanding_amount(db, invoice_id)
    return {"outstanding": outstanding}


def _build_payment_response(payment: Payment, db: Session) -> PaymentResponse:
    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    return PaymentResponse(
        id=payment.id,
        invoice_id=payment.invoice_id,
        invoice_number=invoice.number if invoice else "Unknown",
        method=payment.method,
        amount=payment.amount,
        paid_on=payment.paid_on,
        note=payment.note,
    )