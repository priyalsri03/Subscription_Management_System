"""
Subscription Service - Person 2
Handles subscription lifecycle, pause/resume, line management.
Uses Person 1's services via interfaces.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, List as TypingList

from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta

from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.quotation import QuotationTemplate, QuotationTemplateLine
from backend.app.models.plan import Plan
from backend.app.models.product import Product, ProductVariant
from backend.app.models.tax import Tax
from backend.app.core.interfaces import (
    get_pricing, get_tax, get_plan_repo, get_product_repo,
    AppliedDiscount
)


# Valid status transitions - status -> list of valid next statuses
VALID_TRANSITIONS: Dict[str, list] = {
    "draft": ["quotation", "confirmed", "closed"],
    "quotation": ["confirmed", "draft", "closed"],
    "confirmed": ["active", "quotation", "closed"],
    "active": ["closed"],
    "closed": [],
}


def create_subscription_from_template(
    db: Session,
    template_id: int,
    customer_id: int,
    start_date: date,
    subscription_number: str,
) -> Subscription:
    """Create a subscription from a quotation template."""
    template = db.query(QuotationTemplate).filter(QuotationTemplate.id == template_id).first()
    if not template:
        raise ValueError(f"Template {template_id} not found")

    plan = get_plan_repo().get_plan(db, template.plan_id)
    if not plan:
        raise ValueError(f"Plan {template.plan_id} not found")

    expiry_date = _calculate_expiry_date(start_date, plan.billing_period)

    sub = Subscription(
        number=subscription_number,
        customer_id=customer_id,
        plan_id=plan.id,
        start_date=start_date,
        expiry_date=expiry_date,
        status="draft",
        is_paused=False,
    )
    db.add(sub)
    db.flush()

    for tpl_line in template.lines:
        price = get_pricing().unit_price(db, tpl_line.product_id, tpl_line.variant_id)
        tax_id = _get_product_tax_id(db, tpl_line.product_id)

        line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=tpl_line.product_id,
            variant_id=tpl_line.variant_id,
            quantity=tpl_line.quantity,
            unit_price=price,
            tax_id=tax_id,
            amount=price * tpl_line.quantity,
        )
        db.add(line)

    db.commit()
    db.refresh(sub)
    return sub


def _calculate_expiry_date(start_date: date, billing_period: str) -> date:
    if billing_period == "daily":
        return start_date + timedelta(days=1)
    elif billing_period == "weekly":
        return start_date + timedelta(weeks=1)
    elif billing_period == "monthly":
        return start_date + relativedelta(months=1)
    elif billing_period == "yearly":
        return start_date + relativedelta(years=1)
    return start_date


def _get_product_tax_id(db: Session, product_id: int) -> Optional[int]:
    """Get default tax for a product. TEMP: Returns first tax if exists."""
    tax = db.query(Tax).first()
    return tax.id if tax else None


def transition_status(db: Session, sub: Subscription, new_status: str) -> Subscription:
    """Validate and transition subscription status."""
    current_status = sub.status

    # Validate transition
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise ValueError(f"Invalid transition from {current_status} to {new_status}")

    # Get plan for permission check
    plan = get_plan_repo().get_plan(db, sub.plan_id)

    if new_status == "closed" and not plan.allow_early_close:
        if current_status != "active":
            pass  # Allow closing from non-active states

    sub.status = new_status
    db.commit()
    db.refresh(sub)
    return sub


def pause_subscription(db: Session, sub: Subscription) -> Subscription:
    """Pause an active subscription."""
    plan = get_plan_repo().get_plan(db, sub.plan_id)
    if not plan or not plan.allow_pause:
        raise ValueError("This plan does not allow pausing")
    if sub.status != "active":
        raise ValueError("Only active subscriptions can be paused")
    sub.is_paused = True
    db.commit()
    db.refresh(sub)
    return sub


def resume_subscription(db: Session, sub: Subscription) -> Subscription:
    """Resume a paused subscription."""
    if not sub.is_paused:
        raise ValueError("Subscription is not paused")
    sub.is_paused = False
    db.commit()
    db.refresh(sub)
    return sub


def add_subscription_line(
    db: Session,
    sub: Subscription,
    product_id: int,
    quantity: int,
    variant_id: Optional[int] = None,
    tax_id: Optional[int] = None,
) -> SubscriptionLine:
    """Add a line to a subscription."""
    if sub.status not in ["draft", "quotation"]:
        raise ValueError("Can only add lines to draft or quotation subscriptions")

    price = get_pricing().unit_price(db, product_id, variant_id)
    tax_amt = Decimal("0")
    if tax_id:
        tax_amt = get_tax().calculate_tax(price * quantity, tax_id, db)

    line = SubscriptionLine(
        subscription_id=sub.id,
        product_id=product_id,
        variant_id=variant_id,
        quantity=quantity,
        unit_price=price,
        tax_id=tax_id,
        amount=price * quantity + tax_amt,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


def get_active_subscriptions(db: Session) -> List[Subscription]:
    """Get all active (non-paused) subscriptions."""
    return (
        db.query(Subscription)
        .filter(Subscription.status == "active", Subscription.is_paused == False)
        .all()
    )


def get_subscription_by_number(db: Session, number: str) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.number == number).first()


def is_subscription_due_for_billing(sub: Subscription, on_date: date) -> bool:
    """Check if subscription should be billed on given date."""
    if sub.status != "active":
        return False
    if sub.is_paused:
        return False
    if on_date < sub.start_date:
        return False
    if sub.expiry_date and on_date > sub.expiry_date:
        return False
    return True