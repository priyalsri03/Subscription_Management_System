"""
Product & Variant models - Shared tables (Person 1 owns, Person 2 reads)
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, default="service")
    sales_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    cost_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    notes = Column(Text, nullable=True)

    variants = relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan"
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    attribute = Column(String(50), nullable=False)  # e.g., brand
    value = Column(String(100), nullable=False)     # e.g., Odoo
    extra_price = Column(Numeric(12, 2), nullable=False, default=0.00)

    product = relationship("Product", back_populates="variants")