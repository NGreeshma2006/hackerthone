from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, default="General")
    default_unit = Column(String, default="bags")
    minimum_stock = Column(Float, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    aliases = relationship("ProductAlias", back_populates="product")
    conversions = relationship("UnitConversion", back_populates="product")
    transactions = relationship("StockTransaction", back_populates="product")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    customer_name = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String, default="voice")
    language = Column(String, default="en")

    product = relationship("Product", back_populates="transactions")


class ProductAlias(Base):
    __tablename__ = "product_aliases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    alias = Column(String, nullable=False)
    language = Column(String, default="en")

    product = relationship("Product", back_populates="aliases")


class UnitConversion(Base):
    __tablename__ = "unit_conversions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    from_unit = Column(String, nullable=False)
    to_unit = Column(String, nullable=False)
    conversion_factor = Column(Float, nullable=False)

    product = relationship("Product", back_populates="conversions")


class BusinessSetting(Base):
    __tablename__ = "business_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    business_name = Column(String, default="My Shop")
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
