"""
Tax model - Shared table (Person 1 owns, Person 2 reads)
"""
from sqlalchemy import Column, Integer, String, Numeric

from backend.app.core.db import Base


class Tax(Base):
    __tablename__ = "taxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rate_percent = Column(Numeric(5, 2), nullable=False)  # e.g., 18.00 for 18%