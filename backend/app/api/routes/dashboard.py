"""
Dashboard API - Business overview statistics
Aggregates data from Person 1's models (Products, Plans, Discounts)
and Person 2's models (Subscriptions, Invoices, Payments)
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.app.core.db import get_db
from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.interfaces import User
from backend.app.models.product import Product
from backend.app.models.plan import Plan
from backend.app.models.discount import Discount
from backend.app.models.subscription import Subscription
from backend.app.models.invoice import Invoice
from backend.app.models.payment import Payment


router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


class DashboardStatsResponse(BaseModel):
    total_products: int
    total_plans: int
    total_discounts: int
    active_subscriptions: int
    total_subscriptions: int
    draft_invoices: int
    confirmed_invoices: int
    paid_invoices: int
    total_revenue: Decimal
    outstanding_amount: Decimal
    recent_invoices: list  # Will be populated as needed


class InvoiceBrief(BaseModel):
    id: int
    number: str
    total: Decimal
    status: str
    issue_date: date


class DashboardResponse(BaseModel):
    total_products: int
    total_plans: int
    total_discounts: int
    active_subscriptions: int
    total_subscriptions: int
    total_invoices: int
    draft_invoices: int
    confirmed_invoices: int
    paid_invoices: int
    total_revenue: Decimal
    outstanding_amount: Decimal
    recent_invoices: list


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    as_of_date: Optional[date] = Query(None, description="Date to calculate stats for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics."""
    if as_of_date is None:
        as_of_date = date.today()

    # Product stats
    total_products = db.query(Product).count()

    # Plan stats
    total_plans = db.query(Plan).count()

    # Discount stats
    total_discounts = db.query(Discount).count()

    # Subscription stats
    total_subscriptions = db.query(Subscription).count()
    active_subscriptions = (
        db.query(Subscription)
        .filter(Subscription.status == "active")
        .count()
    )

    # Invoice stats
    total_invoices = db.query(Invoice).count()
    draft_invoices = db.query(Invoice).filter(Invoice.status == "draft").count()
    confirmed_invoices = db.query(Invoice).filter(Invoice.status == "confirmed").count()
    paid_invoices = db.query(Invoice).filter(Invoice.status == "paid").count()

    # Calculate revenue and outstanding
    # Total revenue = sum of all payments received
    total_revenue = db.query(Payment).with_entities(
        Payment.amount
    ).with_entities(
        Payment.amount
    ).all()
    total_revenue = sum([r[0] for r in total_revenue]) if total_revenue else 0

    # Outstanding = sum of invoice totals minus payments
    invoices_with_payments = db.query(Invoice).all()
    outstanding_amount = 0
    for inv in invoices_with_payments:
        payments_for_inv = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
        paid = sum([p.amount for p in payments_for_inv])
        inv_outstanding = float(inv.total) - paid
        if inv_outstanding > 0 and inv.status not in ["cancelled", "closed"]:
            outstanding_amount += inv_outstanding

    # Recent invoices (last 5)
    recent = db.query(Invoice).order_by(Invoice.issue_date.desc()).limit(5).all()
    recent_invoices = [
        {
            "id": inv.id,
            "number": inv.number,
            "total": float(inv.total),
            "status": inv.status,
            "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
        }
        for inv in recent
    ]

    return DashboardResponse(
        total_products=total_products,
        total_plans=total_plans,
        total_discounts=total_discounts,
        active_subscriptions=active_subscriptions,
        total_subscriptions=total_subscriptions,
        total_invoices=total_invoices,
        draft_invoices=draft_invoices,
        confirmed_invoices=confirmed_invoices,
        paid_invoices=paid_invoices,
        total_revenue=Decimal(str(total_revenue)),
        outstanding_amount=Decimal(str(outstanding_amount)),
        recent_invoices=recent_invoices,
    )