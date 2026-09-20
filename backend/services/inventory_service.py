from datetime import datetime
from typing import List, Dict, Optional
from fastapi import HTTPException
import math
from sqlalchemy.orm import Session
from backend.models.models import Product, ProductAlias, StockTransaction, UnitConversion, BusinessSetting
from backend.services.language_service import PRODUCT_ALIASES


class InventoryService:
    DEFAULT_REORDER_LEVEL = 10

    def __init__(self, db: Session):
        self.db = db

    def create_default_business(self):
        setting = self.db.query(BusinessSetting).first()
        if not setting:
            self.db.add(BusinessSetting(business_name="My Shop", preferred_language="en"))
            self.db.commit()

    def get_products(self):
        return self.db.query(Product).all()

    def get_product(self, product_id: str):
        return self.db.query(Product).filter(Product.id == product_id).first()

    def reorder_level_for_product(self, product: Product) -> float:
        """Use 10 units when an item has no explicitly configured level."""
        return product.minimum_stock if product.minimum_stock > 0 else self.DEFAULT_REORDER_LEVEL

    def upsert_product(self, product: Product):
        existing = self.db.query(Product).filter(Product.id == product.id).first()
        if existing:
            existing.name = product.name
            existing.category = product.category
            existing.default_unit = product.default_unit
            existing.minimum_stock = product.minimum_stock
            self.db.commit()
            return existing
        self.db.add(product)
        self.db.commit()
        return product

    def add_alias(self, product_id: str, alias: str, language: str):
        alias_record = ProductAlias(product_id=product_id, alias=alias, language=language)
        self.db.add(alias_record)
        self.db.commit()
        return alias_record

    def add_unit_conversion(self, product_id: str, from_unit: str, to_unit: str, conversion_factor: float):
        record = UnitConversion(product_id=product_id, from_unit=from_unit, to_unit=to_unit, conversion_factor=conversion_factor)
        self.db.add(record)
        self.db.commit()
        return record

    def find_unit_conversion(self, product_id: str, from_unit: str, to_unit: str):
        return self.db.query(UnitConversion).filter_by(product_id=product_id, from_unit=from_unit, to_unit=to_unit).first()

    def activity(self):
        rows = self.db.query(StockTransaction, Product).join(Product, Product.id == StockTransaction.product_id).order_by(StockTransaction.timestamp.desc(), StockTransaction.id.desc()).all()
        return [{"id": tx.id, "title": product.name, "detail": f"{tx.transaction_type.title()} {tx.quantity:g} {tx.unit}", "time": tx.timestamp.strftime("%d %b %H:%M") if tx.timestamp else "", "type": "in" if tx.transaction_type in {"PURCHASE", "RETURN", "FREE_SAMPLE", "ADJUSTMENT"} else "out", "color": "green" if tx.transaction_type in {"PURCHASE", "RETURN", "FREE_SAMPLE", "ADJUSTMENT"} else "orange"} for tx, product in rows]

    def create_transaction(self, product_id: str, quantity: float, unit: str, transaction_type: str, customer_name: str = None, price: float = 0, notes: str = None, source: str = "voice", language: str = "en"):
        product = self.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if transaction_type not in {"PURCHASE", "SALE", "DAMAGE", "RETURN", "CREDIT", "FREE_SAMPLE", "ADJUSTMENT"}:
            raise HTTPException(status_code=400, detail="Unknown stock movement")
        if not math.isfinite(quantity) or (quantity <= 0 and transaction_type != "ADJUSTMENT"):
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
        if unit != product.default_unit:
            conversion = self.db.query(UnitConversion).filter_by(product_id=product_id, from_unit=unit, to_unit=product.default_unit).first()
            if not conversion:
                raise HTTPException(status_code=400, detail=f"Use {product.default_unit} for {product.name}, or configure a unit conversion.")
            quantity *= conversion.conversion_factor
            unit = product.default_unit
        if transaction_type in {"SALE", "DAMAGE", "CREDIT"} and quantity > self.current_stock_for_product(product_id):
            raise HTTPException(status_code=400, detail="Not enough stock for this movement")
        tx = StockTransaction(
            product_id=product_id,
            quantity=quantity,
            unit=unit,
            transaction_type=transaction_type,
            customer_name=customer_name,
            price=price,
            notes=notes,
            source=source,
            language=language,
            timestamp=datetime.utcnow(),
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def current_stock_for_product(self, product_id: str) -> float:
        result = self.db.query(StockTransaction).filter(StockTransaction.product_id == product_id).all()
        total = 0.0
        for tx in result:
            if tx.transaction_type in {"PURCHASE", "RETURN", "FREE_SAMPLE", "ADJUSTMENT"}:
                total += tx.quantity
            else:
                total -= tx.quantity
        return total

    def get_product_story(self, product_id: str):
        product = self.get_product(product_id)
        txs = self.db.query(StockTransaction).filter(StockTransaction.product_id == product_id).order_by(StockTransaction.timestamp.asc()).all()
        current = self.current_stock_for_product(product_id)
        explanation_parts = []
        for tx in txs:
            if tx.transaction_type == "PURCHASE":
                explanation_parts.append(f"received {tx.quantity} {tx.unit}")
            elif tx.transaction_type == "SALE":
                explanation_parts.append(f"sold {tx.quantity} {tx.unit}")
            elif tx.transaction_type == "DAMAGE":
                explanation_parts.append(f"damaged {tx.quantity} {tx.unit}")
            elif tx.transaction_type == "CREDIT":
                explanation_parts.append(f"gave {tx.quantity} {tx.unit} on credit")
        explanation = f"You received {sum(tx.quantity for tx in txs if tx.transaction_type == 'PURCHASE')} {product.default_unit}. "
        explanation += f"{sum(tx.quantity for tx in txs if tx.transaction_type == 'SALE')} were sold, "
        explanation += f"{sum(tx.quantity for tx in txs if tx.transaction_type == 'DAMAGE')} were damaged, and "
        explanation += f"{sum(tx.quantity for tx in txs if tx.transaction_type == 'CREDIT')} were given on credit. "
        explanation += f"{current} {product.default_unit} remain."
        return {
            "product_id": product_id,
            "product_name": product.name,
            "current_stock": current,
            "timeline": [
                {
                    "product_id": product_id,
                    "quantity": tx.quantity,
                    "unit": tx.unit,
                    "transaction_type": tx.transaction_type,
                    "timestamp": tx.timestamp.isoformat() if tx.timestamp else "",
                    "notes": tx.notes,
                }
                for tx in txs
            ],
            "explanation": explanation,
        }

    def get_alerts(self):
        alerts = []
        for product in self.get_products():
            stock = self.current_stock_for_product(product.id)
            reorder_level = self.reorder_level_for_product(product)
            if stock < reorder_level:
                alerts.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "current_stock": stock,
                    "minimum_stock": reorder_level,
                    "status": "CRITICAL",
                })
        return alerts

    def get_insights(self):
        insights = []
        for product in self.get_products():
            stock = self.current_stock_for_product(product.id)
            reorder_level = self.reorder_level_for_product(product)
            usage = sum(tx.quantity for tx in self.db.query(StockTransaction).filter(StockTransaction.product_id == product.id, StockTransaction.transaction_type == 'SALE').all())
            coverage = max(1, stock / usage) if usage else 0
            status = "HEALTHY" if stock >= reorder_level else "CRITICAL"
            insights.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": stock,
                "recent_consumption": usage,
                "minimum_stock": reorder_level,
                "days_of_stock": round(coverage, 1),
                "status": status,
            })
        return insights

    def reconcile_stock(self, product_id: str, physical_quantity: float, unit: str = "bags", notes: str = None):
        recorded = self.current_stock_for_product(product_id)
        difference = physical_quantity - recorded
        adjustment = self.create_transaction(
            product_id=product_id,
            quantity=difference,
            unit=unit,
            transaction_type="ADJUSTMENT",
            notes=notes or f"Reconciliation difference {difference}",
            source="reconcile",
        )
        return {
            "product_id": product_id,
            "recorded": recorded,
            "physical": physical_quantity,
            "difference": difference,
            "adjustment_id": adjustment.id,
        }

    def resolve_product_identifier(self, product_ref: str):
        normalized = product_ref.lower().strip()
        for product in self.get_products():
            if normalized in product.name.lower() or normalized in [alias.alias.lower() for alias in product.aliases]:
                return product.id
        for product_key, aliases in PRODUCT_ALIASES.items():
            if normalized in [a.lower() for a in aliases]:
                for p in self.get_products():
                    if p.name.lower() == product_key.lower() or p.name.lower() in product_key:
                        return p.id
        return None

    def by_product_name(self, name: str):
        product_id = self.resolve_product_identifier(name)
        if product_id:
            return self.get_product(product_id)
        return None
