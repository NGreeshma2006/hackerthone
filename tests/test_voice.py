import os
os.environ['MONGO_URI'] = ''  # Isolated tests never connect to external databases.
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from backend.database import Base, get_db
from backend.models.models import Product, StockTransaction
from backend.services.inventory_service import InventoryService
from backend.services.voice_service import VoiceService, MESSAGES
from backend.services.nlp_service import NLPService
from backend.main import app

class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.inventory = InventoryService(self.db)
        self.inventory.upsert_product(Product(id='rice',name='Rice',default_unit='kg',minimum_stock=3))
        self.inventory.create_transaction('rice',20,'kg','PURCHASE')
        self.voice = VoiceService(self.db)
    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close(); self.engine.dispose()
    def test_all_languages_add_sell_and_query(self):
        examples = {
          'en': ('Add three kg of rice','Sold two kg of rice','How much rice is left?'),
          'hi': ('तीन किलो चावल जोड़ो','दो किलो चावल बेचा','कितना चावल बचा है?'),
          'te': ('మూడు కిలోల బియ్యం జోడించు','రెండు కిలోల బియ్యం అమ్మాను','బియ్యం ఎంత ఉంది?'),
          'ta': ('மூன்று கிலோ அரிசி சேர்','இரண்டு கிலோ அரிசி விற்றேன்','அரிசி எவ்வளவு உள்ளது?'),
          'kn': ('ಮೂರು ಕೆಜಿ ಅಕ್ಕಿ ಸೇರಿಸು','ಎರಡು ಕೆಜಿ ಅಕ್ಕಿ ಮಾರಿದೆ','ಅಕ್ಕಿ ಎಷ್ಟು ಇದೆ?'),
          'ml': ('മൂന്ന് കിലോ അരി ചേർക്കുക','രണ്ട് കിലോ അരി വിറ്റു','അരി എത്ര ഉണ്ട്?'),
          'mr': ('तीन किलो तांदूळ जोडा','दोन किलो तांदूळ विकले','तांदूळ किती शिल्लक आहे?'),
          'bn': ('তিন কেজি চাল যোগ করো','দুই কেজি চাল বিক্রি','চাল কত আছে?'),
        }
        for language, phrases in examples.items():
            with self.subTest(language=language):
                before = self.inventory.current_stock_for_product('rice')
                for phrase in phrases[:2]:
                    result = self.voice.process_voice(phrase, language)
                    self.assertEqual(result['status'],'ok',result)
                    self.assertEqual(result['language'],language)
                    tx = self.db.get(StockTransaction,result['transaction_id'])
                    self.assertEqual(tx.language,language)
                count = self.db.query(StockTransaction).count()
                result = self.voice.process_voice(phrases[2],language)
                self.assertEqual(result['status'],'answer',result)
                self.assertEqual(self.db.query(StockTransaction).count(),count)
                self.assertEqual(self.inventory.current_stock_for_product('rice'),before+1)
                self.assertEqual(result['message'],MESSAGES[language]['stock'].format(product='Rice',stock=f'{before+1:g}',unit=MESSAGES[language]['units']['kg']))
    def test_unknown_negated_ambiguous_and_incomplete_commands_never_write(self):
        for text in ['rice 3 kg','Do not add 3 kg rice','Add -3 kg rice','Add zero kg rice','Add rice','Add 3 kg rice and sell 2 kg rice','How much rice did I sell?', 'Add 3 bags of rice']:
            with self.subTest(text=text):
                before=self.db.query(StockTransaction).count()
                result=self.voice.process_voice(text,'hi')
                self.assertIn(result['status'],['error','answer'],result)
                self.assertEqual(self.db.query(StockTransaction).count(),before)
    def test_low_stock_in_all_languages_is_read_only(self):
        for language,text in [('en','What should I reorder?'),('hi','क्या खरीदना चाहिए?'),('te','ఏమి కొనాలి'),('ta','எதை வாங்க வேண்டும்'),('kn','ಏನು ಖರೀದಿ ಮಾಡಬೇಕು'),('ml','എന്ത് വാങ്ങണം'),('mr','काय खरेदी करायचे'),('bn','কী কিনব')]:
            result=self.voice.process_voice(text,language)
            self.assertEqual(result['status'],'answer',result)
    def test_metric_conversions_default_units_and_native_digits(self):
        for text,expected in [('Add 500 g rice',20.5),('Add २.५ किलो चावल',23),('Add ٣ rice',26)]:
            result=self.voice.process_voice(text,'hi')
            self.assertEqual(result['status'],'ok',result)
            self.assertEqual(self.inventory.current_stock_for_product('rice'),expected)
        self.assertIsNone(NLPService.detect_unit('sugar'))
    def test_product_ambiguity_and_custom_names(self):
        for id,name in [('basmati','Basmati rice'),('soda','7 Up')]:
            self.inventory.upsert_product(Product(id=id,name=name,default_unit='pieces',minimum_stock=0))
        result=self.voice.process_voice('Add 2 pieces of 7 Up','en')
        self.assertEqual(result['status'],'ok',result)
        # A localized generic name cannot silently choose between rice varieties.
        self.assertEqual(self.voice.process_voice('चावल 3 किलो जोड़ो','hi')['status'],'error')
    def test_insufficient_stock_and_packaging_error_are_localized(self):
        for text,key in [('Sell 100 kg rice','insufficient'),('Add 3 bags rice','unitMismatch')]:
            result=self.voice.process_voice(text,'te')
            self.assertEqual(result['status'],'error')
            self.assertEqual(result['message'],MESSAGES['te'][key].format(product='Rice',stock='20',unit=MESSAGES['te']['units']['kg']))

    def test_customer_purchase_reduces_stock_and_confirms_remainder(self):
        result = self.voice.process_voice('Customer bought 2 kg of rice', 'en')
        self.assertEqual(result['status'], 'ok', result)
        self.assertEqual(result['parsed']['transaction_type'], 'SALE')
        self.assertEqual(self.inventory.current_stock_for_product('rice'), 18)
        self.assertEqual(result['message'], 'Saved: sold, 2 kg, Rice. Available: 18 kg.')

    def test_polite_complete_item_entry_creates_a_new_product(self):
        result = self.voice.process_voice('two packets of chocolate pls', 'en')
        self.assertEqual(result['status'], 'ok', result)
        self.assertEqual(result['parsed']['transaction_type'], 'PURCHASE')
        product = self.inventory.by_product_name('chocolate')
        self.assertIsNotNone(product)
        self.assertEqual(self.inventory.current_stock_for_product(product.id), 2)
    def test_new_products_are_created_and_reused(self):
        examples = [('en','Add 10 packets of biscuits','Biscuits','packets'),
                    ('en','Add 5 litres of milk','Milk','litres'),
                    ('en','Add 4 pieces of Dove soap','Dove soap','pieces'),
                    ('hi','तीन किलो नमक जोड़ो','नमक','kg'),
                    ('te','మూడు కిలోల ఉప్పు జోడించు','ఉప్పు','kg'),
                    ('ta','மூன்று கிலோ உப்பு சேர்','உப்பு','kg'),
                    ('kn','ಮೂರು ಕೆಜಿ ಉಪ್ಪು ಸೇರಿಸು','ಉಪ್ಪು','kg'),
                    ('ml','മൂന്ന് കിലോ ഉപ്പ് ചേർക്കുക','ഉപ്പ്','kg'),
                    ('mr','तीन किलो मीठ जोडा','मीठ','kg'),
                    ('bn','তিন কেজি লবণ যোগ করো','লবণ','kg')]
        for language,text,name,unit in examples:
            with self.subTest(language=language,name=name):
                before=self.db.query(Product).count()
                result=self.voice.process_voice(text,language)
                self.assertEqual(result['status'],'ok',result)
                self.assertTrue(result['product_created'])
                product=self.db.query(Product).filter_by(name=name).one()
                self.assertEqual(product.default_unit,unit)
                first=self.inventory.current_stock_for_product(product.id)
                self.assertGreater(first,0)
                result=self.voice.process_voice(text,language)
                self.assertEqual(result['status'],'ok',result)
                self.assertFalse(result['product_created'])
                self.assertEqual(self.db.query(Product).count(),before+1)
                self.assertEqual(self.inventory.current_stock_for_product(product.id),first*2)

    def test_incomplete_new_items_never_create_products(self):
        for text in ['Add soap', 'Add 3 soap', 'Add -2 boxes soap', 'Add 2 boxes',
                     'Add 2 boxes soap and shampoo', 'Sell 2 boxes soap',
                     'How much soap is left?', 'Do not add 2 boxes soap']:
            with self.subTest(text=text):
                before=self.db.query(Product).count()
                result=self.voice.process_voice(text,'en')
                self.assertEqual(result['status'],'error',result)
                self.assertEqual(self.db.query(Product).count(),before)

    def test_http_contract(self):
        def override(): yield self.db
        app.dependency_overrides[get_db] = override
        with TestClient(app) as client:
            response=client.post('/voice/process',json={'text':'How much rice is left?','language':'en'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['status'],'answer')
            self.assertEqual(client.post('/voice/process',json={'text':{'bad':'value'}}).status_code,422)
            self.assertEqual(client.post('/voice/process',json={'text':'Rice','language':'unknown'}).status_code,422)
    def test_translations_are_unicode_and_complete(self):
        for code,translations in MESSAGES.items():
            self.assertEqual(set(translations),set(MESSAGES['en']))
            if code != 'en': self.assertTrue(any(ord(c)>127 for c in translations['saved']))
            self.assertNotIn('??',str(translations))

if __name__ == '__main__': unittest.main()
