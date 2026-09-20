import os
os.environ['MONGO_URI'] = ''  # Isolated tests never connect to external databases.
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.database import Base
from backend.models.models import Product
from backend.services.inventory_service import InventoryService
from backend.services.nlp_service import NLPService
from backend.main import activity

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db=Session(self.engine)
        self.service=InventoryService(self.db)
        self.service.upsert_product(Product(id='rice',name='Rice',category='Grains',default_unit='bags',minimum_stock=2))
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    def test_movement_history_and_reconciliation(self):
        self.service.create_transaction('rice',10,'bags','PURCHASE')
        self.service.create_transaction('rice',3,'bags','SALE')
        self.assertEqual(self.service.current_stock_for_product('rice'),7)
        self.assertEqual(len(activity(self.db)),2)
        self.service.reconcile_stock('rice',4,'bags')
        self.assertEqual(self.service.current_stock_for_product('rice'),4)
        self.assertEqual(len(self.service.get_product_story('rice')['timeline']),3)
    def test_invalid_movements_are_rejected(self):
        for args in [('rice',-1,'bags','PURCHASE'),('rice',2,'kg','PURCHASE'),('missing',2,'bags','PURCHASE'),('rice',2,'bags','SALE')]:
            with self.assertRaises(HTTPException): self.service.create_transaction(*args)
    def test_decimal_voice_quantity(self):
        self.assertEqual(NLPService.parse_voice_input('Add 2.5 bags of rice')['quantity'],2.5)

if __name__=='__main__': unittest.main()
