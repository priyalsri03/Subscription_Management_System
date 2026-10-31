"""
Subscription model - Person 2
"""
from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


# Subscription status constants
class SubscriptionStatus:
    DRAFT = "draft"
    QUOTATION = "quotation"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    CLOSED = "closed"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    payment_terms = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="draft")  # draft, quotation, confirmed, active, closed
    is_paused = Column(Boolean, default=False)

    customer = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan")
    lines = relationship(
        "SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan"
    )
    invoices = relationship("Invoice", back_populates="subscription")


class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_id = Column(Integer, ForeignKey("taxes.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)

    subscription = relationship("Subscription", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    tax = relationship("Tax")