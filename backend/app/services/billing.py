"""
Billing Service - Person 2
Uses Person 1's services via interfaces.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import func
from dateutil.relativedelta import relativedelta

from backend.app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus
from backend.app.models.invoice import Invoice, InvoiceLine
from backend.app.models.payment import Payment
from backend.app.models.discount import Discount
from backend.app.models.tax import Tax
from backend.app.models.product import Product
from backend.app.core.interfaces import (
    get_pricing, get_tax, get_discount, get_user_repo, get_plan_repo
)
from backend.app.core.interfaces import AppliedDiscount


@dataclass
class RevenueSummary:
    invoiced: Decimal
    paid: Decimal
    outstanding: Decimal


@dataclass
class OverdueInvoice:
    id: int
    number: str
    customer_name: str
    customer_email: str
    total: Decimal
    amount_paid: Decimal
    due_date: date
    days_overdue: int


def generate_invoice_for_subscription(
    db: Session,
    subscription_id: int,
    period_start: date,
    period_end: date,
    issue_date: Optional[date] = None,
    due_date: Optional[date] = None,
) -> Invoice:
    """
    Generate an invoice for a subscription for a specific period.
    This prevents double-billing via the unique constraint on (subscription_id, period_start).

    Returns draft invoice. To generate a confirmed invoice, the subscription must be active.
    Active subscription = confirmed status (after draft → quotation → confirmed → active).
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise ValueError(f"Subscription {subscription_id} not found")

    if sub.is_paused:
        raise ValueError("Cannot invoice paused subscription")

    # Only active subscriptions can be invoiced
    if sub.status != SubscriptionStatus.ACTIVE:
        raise ValueError("Can only invoice active subscriptions. Current status: " + sub.status)

    # Check if invoice already exists for this period (double-billing prevention)
    existing = (
        db.query(Invoice)
        .filter(
            Invoice.subscription_id == subscription_id,
            Invoice.period_start == period_start,
        )
        .first()
    )
    if existing:
        raise ValueError(f"Invoice already exists for subscription {sub.number} for period starting {period_start}")

    # Calculate due date based on payment terms if not provided
    if issue_date is None:
        issue_date = date.today()
    if due_date is None:
        # Default to net 30
        due_date = issue_date + timedelta(days=30)
        if sub.payment_terms:
            # Parse payment terms like "net_15", "net_30", "net_60"
            try:
                days = int(sub.payment_terms.replace("net_", ""))
                due_date = issue_date + timedelta(days=days)
            except ValueError:
                pass

    # Build invoice lines from subscription lines
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    invoice_lines = []

    for line in sub.lines:
        line_subtotal = line.unit_price * line.quantity
        subtotal += line_subtotal

        tax_amount = Decimal("0")
        if line.tax_id:
            tax_amount = get_tax().calculate_tax(line_subtotal, line.tax_id, db)
        tax_total += tax_amount

        # Get product name for description
        product = get_plan_repo().get_plan(db, line.product_id) if hasattr(get_plan_repo(), 'get_plan') else None
        from backend.app.models.product import Product as ProductModel
        product = db.query(ProductModel).filter(ProductModel.id == line.product_id).first()

        inv_line = InvoiceLine(
            invoice_id=None,  # Will be set after invoice creation
            product_id=line.product_id,
            description=f"{product.name}" + (f" ({line.variant.value})" if line.variant else ""),
            quantity=line.quantity,
            unit_price=line.unit_price,
            tax_amount=tax_amount,
            amount=line_subtotal + tax_amount,
        )
        invoice_lines.append(inv_line)

    # Find applicable discounts
    applied_discounts = get_discount().find_discounts(
        db=db,
        customer_id=sub.customer_id,
        lines=sub.lines,
        subtotal=subtotal,
        on_date=period_start,
    )
    discount_total = sum(d.amount for d in applied_discounts)

    total = subtotal - discount_total + tax_total

    # Create invoice
    invoice = Invoice(
        number=f"INV-{sub.number}-{period_start.strftime('%Y%m%d')}",
        subscription_id=subscription_id,
        customer_id=sub.customer_id,
        period_start=period_start,
        period_end=period_end,
        issue_date=issue_date,
        due_date=due_date,
        status="draft",
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        total=total,
        amount_paid=Decimal("0"),
    )
    db.add(invoice)
    db.flush()

    # Now set invoice_id on lines and add them
    for inv_line in invoice_lines:
        inv_line.invoice_id = invoice.id
        db.add(inv_line)

    db.commit()
    db.refresh(invoice)

    # Mark discounts as used
    for disc in applied_discounts:
        get_discount().mark_discount_used(db, disc.discount_id)

    return invoice


def run_billing_cycle(db: Session, as_of_date: Optional[date] = None) -> List[Invoice]:
    """
    Generate invoices for all subscriptions due for billing on the given date.
    Returns list of created invoices.
    """
    if as_of_date is None:
        as_of_date = date.today()

    active_subs = (
        db.query(Subscription)
        .filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.is_paused == False,
            Subscription.start_date <= as_of_date,
        )
        .all()
    )

    created_invoices = []
    for sub in active_subs:
        # Determine period based on plan billing period
        plan = get_plan_repo().get_plan(db, sub.plan_id)
        if not plan:
            continue

        # Adjust period_start to the current billing cycle
        # Find the most recent period start <= as_of_date
        current_start = sub.start_date
        while True:
            if plan.billing_period == "daily":
                next_start = current_start + timedelta(days=1)
            elif plan.billing_period == "weekly":
                next_start = current_start + timedelta(weeks=1)
            elif plan.billing_period == "monthly":
                next_start = current_start + relativedelta(months=1)
            elif plan.billing_period == "yearly":
                next_start = current_start + relativedelta(years=1)
            else:
                next_start = current_start + timedelta(days=1)

            if next_start > as_of_date:
                break
            current_start = next_start

        period_start = current_start
        if plan.billing_period == "daily":
            period_end = period_start
        elif plan.billing_period == "weekly":
            period_end = period_start + timedelta(days=6)
        elif plan.billing_period == "monthly":
            period_end = period_start + relativedelta(months=1) - timedelta(days=1)
        elif plan.billing_period == "yearly":
            period_end = period_start + relativedelta(years=1) - timedelta(days=1)
        else:
            period_end = period_start

        # Check if we already invoiced for this period
        existing = (
            db.query(Invoice)
            .filter(
                Invoice.subscription_id == sub.id,
                Invoice.period_start == period_start,
            )
            .first()
        )
        if existing:
            continue

        # Only invoice if period_start <= as_of_date and period_end >= as_of_date
        if period_start <= as_of_date <= period_end:
            try:
                invoice = generate_invoice_for_subscription(
                    db=db,
                    subscription_id=sub.id,
                    period_start=period_start,
                    period_end=period_end,
                    issue_date=as_of_date,
                )
                created_invoices.append(invoice)
            except ValueError:
                # Skip if any validation fails
                continue

    return created_invoices


# Dashboard functions (Person 2 provides these for the dashboard)
def active_subscription_count(db: Session) -> int:
    """Return count of active (non-paused) subscriptions."""
    return (
        db.query(Subscription)
        .filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.is_paused == False,
        )
        .count()
    )


def revenue_summary(db: Session, date_from: date, date_to: date) -> RevenueSummary:
    """Return invoiced, paid, and outstanding amounts in date range."""
    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.issue_date >= date_from,
            Invoice.issue_date <= date_to,
            Invoice.status != "cancelled",
        )
        .all()
    )

    invoiced = Decimal("0")
    paid = Decimal("0")
    for inv in invoices:
        invoiced += inv.total
        paid += inv.amount_paid

    return RevenueSummary(
        invoiced=invoiced,
        paid=paid,
        outstanding=invoiced - paid,
    )


def overdue_invoices(db: Session) -> List[OverdueInvoice]:
    """Return list of overdue invoices with details."""
    today = date.today()
    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.status == "confirmed",
            Invoice.due_date < today,
            Invoice.amount_paid < Invoice.total,
        )
        .all()
    )

    result = []
    for inv in invoices:
        days_overdue = (today - inv.due_date).days
        # Get customer via user repo
        user = get_user_repo().get_user(db, inv.customer_id)
        result.append(
            OverdueInvoice(
                id=inv.id,
                number=inv.number,
                customer_name=user.name if user else "Unknown",
                customer_email=user.email if user else "Unknown",
                total=inv.total,
                amount_paid=inv.amount_paid,
                due_date=inv.due_date,
                days_overdue=days_overdue,
            )
        )

    # Sort by most overdue first
    result.sort(key=lambda x: x.days_overdue, reverse=True)
    return result