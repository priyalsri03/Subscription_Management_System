"""
Discount model - Shared table (Person 1 owns, Person 2 reads/writes usage)
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey

from backend.app.core.db import Base


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    kind = Column(String(20), nullable=False)  # fixed or percent
    value = Column(Numeric(12, 2), nullable=False)
    min_purchase = Column(Numeric(12, 2), nullable=True)
    min_quantity = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    times_used = Column(Integer, default=0, nullable=False)
    applies_to = Column(String(20), nullable=False)  # product or subscription
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)