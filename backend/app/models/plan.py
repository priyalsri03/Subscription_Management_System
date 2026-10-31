"""
Plan model - Shared table (Person 1 owns, Person 2 reads)
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean

from backend.app.core.db import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0.00)
    billing_period = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    min_quantity = Column(Integer, nullable=False, default=1)
    available_from = Column(Date, nullable=True)
    available_to = Column(Date, nullable=True)
    auto_close = Column(Boolean, default=False)
    allow_early_close = Column(Boolean, default=True)
    allow_pause = Column(Boolean, default=True)
    allow_renew = Column(Boolean, default=True)