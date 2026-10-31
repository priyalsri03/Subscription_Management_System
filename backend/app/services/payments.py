from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.invoice import Invoice
from backend.app.models.payment import Payment


def record_payment(
    db: Session,
    invoice_id: int,
    amount: Decimal,
    method: str,
    paid_on: Optional[date] = None,
    note: Optional[str] = None,
) -> Payment:
    """
    Record a payment against an invoice.
    Auto-updates invoice status to 'paid' when amount_paid >= total.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    if invoice.status == "cancelled":
        raise ValueError("Cannot record payment on cancelled invoice")

    if paid_on is None:
        paid_on = date.today()

    payment = Payment(
        invoice_id=invoice_id,
        method=method,
        amount=amount,
        paid_on=paid_on,
        note=note,
    )
    db.add(payment)

    # Update invoice
    invoice.amount_paid += amount
    if invoice.amount_paid >= invoice.total:
        invoice.status = "paid"
        invoice.amount_paid = invoice.total  # Cap at total

    db.commit()
    db.refresh(payment)
    return payment


def get_invoice_payments(db: Session, invoice_id: int):
    """Get all payments for an invoice."""
    return (
        db.query(Payment)
        .filter(Payment.invoice_id == invoice_id)
        .order_by(Payment.paid_on.desc())
        .all()
    )


def get_outstanding_amount(db: Session, invoice_id: int) -> Decimal:
    """Get outstanding amount for an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")
    return invoice.total - invoice.amount_paid