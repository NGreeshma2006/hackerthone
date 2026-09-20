"""Extract a new item name from a single, explicit stock-receipt command."""
import re
import unicodedata
from backend.services.nlp_service import NUMBER_WORDS, contains
from backend.services.voice_vocabulary import ACTIONS, UNITS

# These are command words, not a product allowlist. Names such as soap,
# biscuits, detergent, milk, and brands can be stored without pre-registration.
FILLER = ['please', 'of', 'today', 'i', 'we', 'have', 'has', 'just', 'stock', 'inventory', 'new product', 'new item', 'product', 'item', 'to my shop', 'to inventory', 'to stock', 'were', 'was', 'is', 'in', 'the', 'aaj', 'aaj ki', 'कृपया', 'आज', 'नया सामान', 'नई वस्तु', 'स्टॉक में', 'में', 'का', 'की', 'के', 'है', 'हैं', 'मैंने', 'మా', 'ఈరోజు', 'దయచేసి', 'నేడు', 'కొత్త', 'இன்று', 'தயவுசெய்து', 'புதிய', 'ಇಂದು', 'ದಯವಿಟ್ಟು', 'ಹೊಸ', 'ഇന്ന്', 'ദയവായി', 'പുതിയ', 'कृपया', 'आज', 'नवीन', 'आजचा', 'আজ', 'দয়া করে', 'নতুন', 'করো', 'করুন']
CONNECTORS = ['and', 'plus', 'और', 'तथा', 'మరియు', 'மற்றும்', 'ಹಾಗೂ', 'ಮತ್ತು', 'കൂടാതെ', 'आणि', 'এবং', '&']

def remove_phrase(text, phrase):
    def replace(match):
        before=text[match.start()-1] if match.start() else ' '
        after=text[match.end()] if match.end()<len(text) else ' '
        if any(c.isalnum() or unicodedata.category(c).startswith('M') for c in (before,after)):
            return match.group()
        return ' '
    return re.sub(re.escape(phrase),replace,text,flags=re.IGNORECASE)

def extract_new_product(text):
    text=unicodedata.normalize('NFC',text).strip()
    if any(contains(text, word) for word in CONNECTORS):
        return None
    phrases = [*FILLER, *NUMBER_WORDS, *[p for group in ACTIONS.values() for p in group], *[p for group in UNITS.values() for p in group]]
    for phrase in sorted(set(phrases),key=len,reverse=True):
        text=remove_phrase(text,phrase)
    text=re.sub(r'(?<!\w)[+-]?\d+(?:\.\d+)?(?!\w)',' ',text)
    name=' '.join(text.strip(' .,!?।:;\"\'“”').split())
    if not name or len(name)>100 or len(name.split())>8 or not any(c.isalpha() for c in name):
        return None
    if any(c in name for c in '?!;:'):
        return None
    return name[0].upper()+name[1:]
