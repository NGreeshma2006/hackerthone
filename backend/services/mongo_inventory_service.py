"""MongoDB implementation of the inventory store.

The public methods intentionally mirror ``InventoryService`` so API callers do
not need to know which persistence engine is active.
"""
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4
import math

from fastapi import HTTPException
from pymongo import DESCENDING

from backend.services.language_service import PRODUCT_ALIASES


class MongoInventoryService:
    DEFAULT_REORDER_LEVEL = 10

    def __init__(self, db):
        self.db = db
        self.products = db.products
        self.transactions = db.stock_transactions
        self.aliases = db.product_aliases
        self.conversions = db.unit_conversions
        self.settings = db.business_settings

    @staticmethod
    def _object(record):
        if record is None:
            return None
        record = dict(record)
        record.pop('_id', None)
        return SimpleNamespace(**record)

    def _product(self, record):
        product = self._object(record)
        if product:
            product.aliases = [self._object(a) for a in self.aliases.find({'product_id': product.id})]
        return product

    def create_default_business(self):
        self.settings.update_one({}, {'$setOnInsert': {'business_name': 'My Shop', 'preferred_language': 'en', 'created_at': datetime.utcnow()}}, upsert=True)

    def get_products(self):
        return [self._product(product) for product in self.products.find().sort('name', 1)]

    def get_product(self, product_id):
        return self._product(self.products.find_one({'id': product_id}))

    def reorder_level_for_product(self, product):
        return product.minimum_stock if product.minimum_stock > 0 else self.DEFAULT_REORDER_LEVEL

    def upsert_product(self, product):
        record = {
            'id': product.id, 'name': product.name, 'category': product.category,
            'default_unit': product.default_unit, 'minimum_stock': product.minimum_stock,
            'created_at': getattr(product, 'created_at', None) or datetime.utcnow(),
        }
        self.products.update_one({'id': product.id}, {'$set': record}, upsert=True)
        return self.get_product(product.id)

    def add_alias(self, product_id, alias, language):
        if not self.get_product(product_id):
            raise HTTPException(status_code=404, detail='Product not found')
        record = {'id': str(uuid4()), 'product_id': product_id, 'alias': alias, 'language': language}
        self.aliases.update_one({'product_id': product_id, 'alias': alias}, {'$setOnInsert': record}, upsert=True)
        return self._object(record)

    def add_unit_conversion(self, product_id, from_unit, to_unit, conversion_factor):
        if not self.get_product(product_id):
            raise HTTPException(status_code=404, detail='Product not found')
        record = {'id': str(uuid4()), 'product_id': product_id, 'from_unit': from_unit, 'to_unit': to_unit, 'conversion_factor': conversion_factor}
        self.conversions.update_one({'product_id': product_id, 'from_unit': from_unit, 'to_unit': to_unit}, {'$set': record}, upsert=True)
        return self._object(record)

    def find_unit_conversion(self, product_id, from_unit, to_unit):
        return self._object(self.conversions.find_one({'product_id': product_id, 'from_unit': from_unit, 'to_unit': to_unit}))

    def create_transaction(self, product_id, quantity, unit, transaction_type, customer_name=None, price=0, notes=None, source='voice', language='en'):
        product = self.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail='Product not found')
        if transaction_type not in {'PURCHASE', 'SALE', 'DAMAGE', 'RETURN', 'CREDIT', 'FREE_SAMPLE', 'ADJUSTMENT'}:
            raise HTTPException(status_code=400, detail='Unknown stock movement')
        if not math.isfinite(quantity) or (quantity <= 0 and transaction_type != 'ADJUSTMENT'):
            raise HTTPException(status_code=400, detail='Quantity must be greater than zero')
        if unit != product.default_unit:
            conversion = self.conversions.find_one({'product_id': product_id, 'from_unit': unit, 'to_unit': product.default_unit})
            if not conversion:
                raise HTTPException(status_code=400, detail=f'Use {product.default_unit} for {product.name}, or configure a unit conversion.')
            quantity *= conversion['conversion_factor']
            unit = product.default_unit
        if transaction_type in {'SALE', 'DAMAGE', 'CREDIT'} and quantity > self.current_stock_for_product(product_id):
            raise HTTPException(status_code=400, detail='Not enough stock for this movement')
        record = {'id': str(uuid4()), 'product_id': product_id, 'quantity': quantity, 'unit': unit, 'transaction_type': transaction_type, 'customer_name': customer_name, 'price': price, 'notes': notes, 'source': source, 'language': language, 'timestamp': datetime.utcnow()}
        self.transactions.insert_one(record)
        return self._object(record)

    def current_stock_for_product(self, product_id):
        total = 0.0
        for tx in self.transactions.find({'product_id': product_id}):
            total += tx['quantity'] if tx['transaction_type'] in {'PURCHASE', 'RETURN', 'FREE_SAMPLE', 'ADJUSTMENT'} else -tx['quantity']
        return total

    def get_product_story(self, product_id):
        product = self.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail='Product not found')
        txs = list(self.transactions.find({'product_id': product_id}).sort('timestamp', 1))
        totals = {kind: sum(tx['quantity'] for tx in txs if tx['transaction_type'] == kind) for kind in ('PURCHASE', 'SALE', 'DAMAGE', 'CREDIT')}
        current = self.current_stock_for_product(product_id)
        return {'product_id': product_id, 'product_name': product.name, 'current_stock': current,
                'timeline': [{k: tx.get(k) for k in ('product_id', 'quantity', 'unit', 'transaction_type', 'notes')} | {'timestamp': tx['timestamp'].isoformat() if tx.get('timestamp') else ''} for tx in txs],
                'explanation': f"You received {totals['PURCHASE']} {product.default_unit}. {totals['SALE']} were sold, {totals['DAMAGE']} were damaged, and {totals['CREDIT']} were given on credit. {current} {product.default_unit} remain."}

    def get_alerts(self):
        alerts = []
        for product in self.get_products():
            stock, level = self.current_stock_for_product(product.id), self.reorder_level_for_product(product)
            if stock < level:
                alerts.append({'product_id': product.id, 'product_name': product.name, 'current_stock': stock, 'minimum_stock': level, 'status': 'CRITICAL'})
        return alerts

    def get_insights(self):
        insights = []
        for product in self.get_products():
            stock, level = self.current_stock_for_product(product.id), self.reorder_level_for_product(product)
            usage = sum(tx['quantity'] for tx in self.transactions.find({'product_id': product.id, 'transaction_type': 'SALE'}))
            insights.append({'product_id': product.id, 'product_name': product.name, 'current_stock': stock, 'recent_consumption': usage, 'minimum_stock': level, 'days_of_stock': round(max(1, stock / usage), 1) if usage else 0, 'status': 'HEALTHY' if stock >= level else 'CRITICAL'})
        return insights

    def reconcile_stock(self, product_id, physical_quantity, unit='bags', notes=None):
        recorded = self.current_stock_for_product(product_id)
        tx = self.create_transaction(product_id, physical_quantity - recorded, unit, 'ADJUSTMENT', notes=notes or f'Reconciliation difference {physical_quantity - recorded}', source='reconcile')
        return {'product_id': product_id, 'recorded': recorded, 'physical': physical_quantity, 'difference': physical_quantity - recorded, 'adjustment_id': tx.id}

    def resolve_product_identifier(self, product_ref):
        normalized = product_ref.lower().strip()
        for product in self.get_products():
            if normalized in product.name.lower() or normalized in [alias.alias.lower() for alias in product.aliases]:
                return product.id
        for key, aliases in PRODUCT_ALIASES.items():
            if normalized in [alias.lower() for alias in aliases]:
                match = self.products.find_one({'name': {'$regex': f'^{key}$', '$options': 'i'}})
                if match:
                    return match['id']
        return None

    def by_product_name(self, name):
        product_id = self.resolve_product_identifier(name)
        return self.get_product(product_id) if product_id else None

    def activity(self):
        rows = []
        for tx in self.transactions.find().sort([('timestamp', DESCENDING), ('id', DESCENDING)]):
            product = self.get_product(tx['product_id'])
            if product:
                incoming = tx['transaction_type'] in {'PURCHASE', 'RETURN', 'FREE_SAMPLE', 'ADJUSTMENT'}
                rows.append({'id': tx['id'], 'title': product.name, 'detail': f"{tx['transaction_type'].title()} {tx['quantity']:g} {tx['unit']}", 'time': tx['timestamp'].strftime('%d %b %H:%M') if tx.get('timestamp') else '', 'type': 'in' if incoming else 'out', 'color': 'green' if incoming else 'orange'})
        return rows
