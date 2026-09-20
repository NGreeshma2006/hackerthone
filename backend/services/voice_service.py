import json
import math
from uuid import uuid4
from pathlib import Path
from fastapi import HTTPException
from backend.services.nlp_service import NLPService, contains
from backend.services.voice_vocabulary import PRODUCTS, UNITS
from backend.services.inventory_service import InventoryService
from backend.models.models import Product
from backend.services.new_product_service import extract_new_product

MESSAGES = json.loads((Path(__file__).resolve().parents[2] / 'shared' / 'voice_messages.json').read_text(encoding='utf-8'))

class VoiceService:
    def __init__(self, store):
        self.inventory_service = store if hasattr(store, 'get_products') else InventoryService(store)

    def process_voice(self, text: str, selected_language: str = 'en'):
        language = selected_language if selected_language in MESSAGES else 'en'
        messages = MESSAGES[language]
        parsed = NLPService.parse_voice_input(text)
        parsed['language'] = language

        def reply(key, status='error', **values):
            return {'status': status, 'message': messages[key].format(**values), 'parsed': parsed, 'language': language}

        def unit_label(unit):
            return messages['units'].get(unit, unit)

        if parsed['intent'] == 'INVALID':
            return reply('invalid')
        products = self.inventory_service.get_products()
        if parsed['intent'] == 'LOW_STOCK':
            low = [p for p in products if self.inventory_service.current_stock_for_product(p.id) < self.inventory_service.reorder_level_for_product(p)]
            items = ', '.join(f'{p.name}: {self.inventory_service.current_stock_for_product(p.id):g} {unit_label(p.default_unit)}' for p in low)
            return reply('low' if low else 'healthy', status='answer', items=items)

        # Prefer explicit full names and shop aliases over generic product families.
        direct = [(len(alias), p) for p in products for alias in [p.name, *[a.alias for a in p.aliases]] if contains(text, alias)]
        candidates = []
        if direct:
            longest = max(length for length, p in direct)
            candidates = list({p.id: p for length, p in direct if length == longest}.values())
            # Naming two separate products in one movement is not a single entry.
            named = {p.id for length, p in direct}
            if len(named) > 1 and parsed['intent'] == 'MOVEMENT':
                return reply('multiple')
        else:
            families = [family for family, aliases in PRODUCTS.items() if any(contains(text, alias) for alias in aliases)]
            if len(families) > 1:
                return reply('multiple')
            if families:
                aliases = [families[0], *PRODUCTS[families[0]]]
                candidates = [p for p in products if any(contains(p.name, a) for a in aliases)]
        new_product = False
        if not candidates:
            # An explicit receipt can introduce any named product. Queries,
            # sales and incomplete requests never create empty catalog entries.
            if parsed['intent'] != 'MOVEMENT' or parsed['transaction_type'] != 'PURCHASE':
                return reply('product')
            name = extract_new_product(text)
            if not name or not parsed['unit']:
                return reply('product')
            candidates = [Product(id=str(uuid4()), name=name, category='General',
                                  default_unit=parsed['unit'], minimum_stock=10)]
            new_product = True
        if len(candidates) > 1:
            return reply('ambiguous', items=', '.join(p.name for p in candidates))
        product = candidates[0]
        parsed['product'] = product.name
        current = self.inventory_service.current_stock_for_product(product.id)
        values = {'product': product.name, 'stock': f'{current:g}', 'unit': unit_label(product.default_unit)}
        if parsed['intent'] == 'INQUIRY':
            return reply('stock', status='answer', **values)
        if parsed['intent'] != 'MOVEMENT' or parsed['transaction_type'] not in messages['actions']:
            return reply('action')
        # Ignore numbers that are part of a catalog name, such as '7 Up'.
        quantity_text = text.casefold().replace(product.name.casefold(), ' ')
        quantities = NLPService.quantities(quantity_text)
        if len(quantities) > 1:
            return reply('multiple')
        quantity = quantities[0] if quantities else None
        if quantity is None or quantity <= 0 or not math.isfinite(quantity):
            return reply('quantity')
        parsed['quantity'] = quantity
        unit = parsed['unit'] or product.default_unit
        target_unit = NLPService.detect_unit(product.default_unit) or product.default_unit
        # Canonical spelling and unambiguous metric conversions; packaging needs a shop conversion.
        if unit == target_unit:
            unit = product.default_unit
        if unit != product.default_unit:
            metric = {('g', 'kg'): .001, ('kg', 'g'): 1000, ('ml', 'litres'): .001, ('litres', 'ml'): 1000}
            conversion = self.inventory_service.find_unit_conversion(product.id, unit, product.default_unit)
            factor = conversion.conversion_factor if conversion else metric.get((unit, target_unit))
            if factor is None or not math.isfinite(factor) or factor <= 0:
                return reply('unitMismatch', **values)
            quantity *= factor
            unit = product.default_unit
        parsed['unit'] = unit
        parsed['quantity'] = quantity
        if parsed['transaction_type'] in {'SALE', 'DAMAGE', 'CREDIT'} and quantity > current:
            return reply('insufficient', **values)
        try:
            if new_product:
                self.inventory_service.upsert_product(product)
            transaction = self.inventory_service.create_transaction(
                product_id=product.id, quantity=quantity, unit=unit,
                transaction_type=parsed['transaction_type'], notes=text,
                source='voice', language=language)
        except HTTPException:
            return reply('invalid')
        values['stock'] = f'{self.inventory_service.current_stock_for_product(product.id):g}'
        result = reply('saved', status='ok', action=messages['actions'][parsed['transaction_type']], quantity=f'{quantity:g}', **values)
        result['transaction_id'] = transaction.id
        result['product_created'] = new_product
        return result
