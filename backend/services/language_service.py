SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "te": "తెలుగు",
    "ta": "தமிழ்",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "mr": "मराठी",
    "bn": "বাংলা",
}

PRODUCT_ALIASES = {
    "rice": ["rice", "chawal", "चावल", "బియ్యం", "அரிசி", "ಅарಿಶಿ", "तांदूळ", "ভাত", "চালের", "rice bag", "arisi"],
    "oil": ["oil", "तेल", "నూనె", "எண்ணெய்", "ಎಣ್ಣೆ", "തേൻ", "तेल", "তেল", "oil packet", "fortune oil"],
    "sugar": ["sugar", "चीनी", "చక్కెర", "சக்கரை", "ಸಕ್ಕರೆ", "പഞ്ചസാര", "साखर", "চিনি"],
    "dal": ["dal", "दाल", "పప్పు", "துவரம் பருப்பு", "ಉಡುಪಿ", "പയർ", "दाल", "ডাল"],
    "wheat": ["wheat", "गेहूँ", "గోధుమ", "கோதுமை", "ಗೋಧಿ", "ഗോതം", "गहू", "গম"],
}

# Common forms returned by speech recognition that are not covered by the
# original shop vocabulary.  These keep the same language-independent product
# id, so stock added in any language contributes to one total.
PRODUCT_ALIASES["rice"].extend(["চাল", "അരി", "ಅಕ್ಕಿ"])

UNIT_ALIASES = {
    "bags": ["bags", "bag", "bori", "बोरी", "బోరా", "பை", "ಬ್ಯಾಗ್", "ബാഗ്", "বস্তা", "packet"],
    "kg": ["kg", "kilogram", "kilograms", "kilo", "किलो", "కిలో", "கிலோ", "ಕೆಜಿ", "കിലോ", "किलो", "কেজি"],
    "g": ["gram", "grams", "g", "ग्राम", "గ్రామ్", "கிராம்", "ಗ್ರಾಂ", "ഗ്രാം", "গ্রাম"],
    "litres": ["litre", "litres", "liter", "liters", "लीटर", "లీటరు", "லிட்டர்", "ಲೀಟರ್", "ലിറ്റർ", "लीटर", "লিটার"],
    "ml": ["ml", "millilitre", "millilitres", "मिली", "మిల్లీ", "மில்லி", "ಮಿಲಿ", "മില്ലി"],
    "cartons": ["carton", "cartons", "కార్ట్న్", "கார்டன்", "ಕಾರ್ಟನ್", "कार्टन", "কার্টন"],
    "boxes": ["box", "boxes", "பெட்டி", "ಬಾಕ್ಸ್", "ബോക്‌സ്", "বক্স"],
    "pieces": ["piece", "pieces", "pcs", "टुकड़ा", "టుక్కు", "துண்டு", "ತುಣುಕು", "ടൈം", "পিস"],
    "dozens": ["dozen", "dozens", "দশ", "ಡ즌್", "டஜன்"],
    "quintals": ["quintal", "quintals", "क्विंटल", "క్వింటాల్", "குவிண்டால்", "ಕ್ವಿಂಟಾಲ್", "ക്വിന്റൽ", "কুইন্টাল"],
}

ACTION_KEYWORDS = {
    "PURCHASE": ["came", "arrived", "aaya", "आया", "వచ్చింది", "வந்தது", "ಬಂತು", "വന്നു", "आला", "এসেছে", "add", "purchase", "bought", "buy"],
    "SALE": ["sold", "sell", "becha", "बेचा", "అమ్మారు", "விற்கப்பட்டது", "ಮಾರಿದ", "വിൽപ്പന", "sold out", "sale"],
    "DAMAGE": ["damaged", "damage", "broken", "kharab", "नुकसान", "పొడిచిపోయింది", "சேதமடைந்தது", "ನಾಶವಾಯಿತು", "തകർന്നു", "ক্ষতি", "ভাঙা"],
    "RETURN": ["returned", "return", "wapis", "वापस", "తిరిగి", "திரும்பியது", "ಹಿಂತಿರುಗಿದ", "ফিরে", "বাড়ি"],
    "CREDIT": ["credit", "given on credit", "loan", "उधार", "వడా", "கடன்", "ಕ್ರೆಡಿಟ್", "ধারে"],
    "FREE_SAMPLE": ["free sample", "sample", "नमूना", "సంప samples", "மாதிரி", "ಮಾದರಿ", "স্যাম্পল"],
    "ADJUSTMENT": ["adjust", "reconcile", "counted", "count", "गिनती", "గణన", "எண்ணிக்கை", "ಎಣಿಕೆ", "গণনা"],
}

TRANSACTION_TYPE_MAP = {
    "PURCHASE": "PURCHASE",
    "SALE": "SALE",
    "DAMAGE": "DAMAGE",
    "RETURN": "RETURN",
    "CREDIT": "CREDIT",
    "FREE_SAMPLE": "FREE_SAMPLE",
    "ADJUSTMENT": "ADJUSTMENT",
}


def normalize_language(code: str) -> str:
    return (code or "en").lower()


def detect_language(text: str) -> str:
    lowered = (text or "").lower()
    if any(token in lowered for token in ["आज", "चावल", "बोरी", "है", "कितना", "मात्रा"]):
        return "hi"
    if any(token in lowered for token in ["బియ్యం", "చాల", "ఎంత", "వచ్చింది", "బోరా"]):
        return "te"
    if any(token in lowered for token in ["அரிசி", "எவ்வளவு", "வந்தது", "பை", "கடன்"]):
        return "ta"
    if any(token in lowered for token in ["ಅರಿಶಿ", "ಎಷ್ಟು", "ಬಂದಿತು", "ಬ್ಯಾಗ್", "ಫೋರ್ಚೂನ್"]):
        return "kn"
    if any(token in lowered for token in ["അരിയ", "എത്ര", "വന്നത്", "ബാഗ്", "തെളിയാം"]):
        return "ml"
    if any(token in lowered for token in ["चावल", "आज", "बोरी", "कितना", "आला"]):
        return "mr"
    if any(token in lowered for token in ["চাল", "আজ", "বস্তা", "কত", "এসেছে"]):
        return "bn"
    return "en"
