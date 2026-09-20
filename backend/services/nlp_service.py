import re
import unicodedata
from typing import Dict, Optional
from backend.services.language_service import detect_language
from backend.services.voice_vocabulary import PRODUCTS, UNITS, ACTIONS, QUERY, LOW, NEGATION

NUMBER_WORDS = {}
for words in [
    'one two three four five six seven eight nine ten',
    'ek do teen char paanch che saat aath nau das',
    'एक दो तीन चार पाँच छह सात आठ नौ दस',
    'ఒకటి రెండు మూడు నాలుగు ఐదు ఆరు ఏడు ఎనిమిది తొమ్మిది పది',
    'ஒன்று இரண்டு மூன்று நான்கு ஐந்து ஆறு ஏழு எட்டு ஒன்பது பத்து',
    'ಒಂದು ಎರಡು ಮೂರು ನಾಲ್ಕು ಐದು ಆರು ಏಳು ಎಂಟು ಒಂಬತ್ತು ಹತ್ತು',
    'ഒന്ന് രണ്ട് മൂന്ന് നാല് അഞ്ച് ആറ് ഏഴ് എട്ട് ഒമ്പത് പത്ത്',
    'एक दोन तीन चार पाच सहा सात आठ नऊ दहा',
    'এক দুই তিন চার পাঁচ ছয় সাত আট নয় দশ',
]:
    NUMBER_WORDS.update({word: i for i, word in enumerate(words.split(), 1)})
NUMBER_WORDS.update({'पांच': 5, 'ఒక': 1, 'ஒரு': 1, 'zero': 0, 'शून्य': 0, 'सौ':100, 'hundred':100, 'twenty':20, 'बीस':20, 'ఇరవై':20, 'இருபது':20, 'ಇಪ್ಪತ್ತು':20, 'ഇരുപത്':20, 'वीस':20, 'কুড়ি':20})

def contains(text, phrase):
    # Unicode combining marks belong to the surrounding word as well.
    text = unicodedata.normalize('NFC', text).casefold()
    phrase = unicodedata.normalize('NFC', phrase).casefold()
    for match in re.finditer(re.escape(phrase), text):
        before = text[match.start()-1] if match.start() else ' '
        after = text[match.end()] if match.end() < len(text) else ' '
        if not any(c.isalnum() or unicodedata.category(c).startswith('M') for c in (before, after)):
            return True
    return False

class NLPService:
    @staticmethod
    def normalize_text(text):
        return unicodedata.normalize('NFC', text).casefold().strip()

    @staticmethod
    def detect_product(text) -> Optional[str]:
        matches = [(len(alias), key) for key, aliases in PRODUCTS.items() for alias in aliases if contains(text, alias)]
        return max(matches)[1] if matches else None

    @staticmethod
    def detect_unit(text) -> Optional[str]:
        matches = [(len(alias), key) for key, aliases in UNITS.items() for alias in aliases if contains(text, alias)]
        return max(matches)[1] if matches else None

    @staticmethod
    def quantities(text):
        normalized = ''.join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in text)
        values = [float(n) for n in re.findall(r'(?<!\w)[+-]?\d+(?:\.\d+)?(?!\w)', normalized)]
        values += [float(value) for word, value in NUMBER_WORDS.items() for _ in range(len(re.findall(r'(?<!\w)' + re.escape(word) + r'(?!\w)', normalized.casefold())))]
        return values

    @staticmethod
    def extract_quantity(text):
        values = NLPService.quantities(text)
        return values[0] if len(values) == 1 else None

    @staticmethod
    def detect_transaction_type(text):
        # "Customer bought" describes stock leaving the shop, even though the
        # word "bought" on its own means the shop received stock.
        if any(contains(text, phrase) for phrase in ('customer bought', 'customer purchased', 'customer purchase')):
            return 'SALE'
        matches = [key for key, words in ACTIONS.items() if any(contains(text, word) for word in words)]
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def parse_voice_input(text) -> Dict:
        normalized = NLPService.normalize_text(text)
        action = NLPService.detect_transaction_type(normalized)
        inquiry = any(contains(normalized, word) for word in QUERY)
        low = any(contains(normalized, word) for word in LOW)
        negated = any(contains(normalized, word) for word in NEGATION)
        quantity = NLPService.extract_quantity(text)
        unit = NLPService.detect_unit(text)
        # A complete polite item entry ("two packets of chocolate please") is
        # a common hands-free way to record received stock. Require both a
        # quantity and unit so an unclear sentence can never change stock.
        polite_entry = not action and quantity is not None and unit is not None and any(
            contains(normalized, word) for word in ('please', 'pls', 'kindly', 'कृपया', 'దయచేసి', 'தயவுசெய்து', 'ದಯವಿಟ್ಟು', 'ദയവായി', 'দয়া করে')
        )
        if polite_entry:
            action = 'PURCHASE'
        # Questions are read-only even if they mention a sale or purchase.
        intent = 'INVALID' if negated else 'LOW_STOCK' if low else 'INQUIRY' if inquiry else 'MOVEMENT' if action else 'UNKNOWN'
        return {'intent': intent, 'product': NLPService.detect_product(normalized),
                'quantity': quantity, 'unit': unit,
                'transaction_type': action, 'language': detect_language(text), 'raw_text': text}
