"""Explicit inventory vocabulary; unknown phrases never default to a purchase."""
from backend.services.language_service import PRODUCT_ALIASES, UNIT_ALIASES, ACTION_KEYWORDS

PRODUCTS = {key: list(values) for key, values in PRODUCT_ALIASES.items()}
PRODUCTS['rice'] += ['chaval', 'chawal', 'चावल', 'तांदूळ', 'బియ్యాన్ని']
PRODUCTS['dal'] += ['toor dal', 'तूर दाल', 'துவரம் பருப்பு', 'పప్పు', 'ಬೇಳೆ', 'പരിപ്പ്', 'डाळ']
PRODUCTS['oil'] += ['tel', 'എണ്ണ']
PRODUCTS['sugar'] += ['chini', 'சர்க்கரை']
PRODUCTS['wheat'] += ['gehu', 'गेहूं', 'ഗോതമ്പ്']
# Remove unrelated or erroneous sample aliases.
for key, wrong in {'rice':['ಅарಿಶಿ'], 'oil':['തേൻ'], 'dal':['ಉಡುಪಿ']}.items():
    PRODUCTS[key] = [a for a in PRODUCTS[key] if a not in wrong]
UNITS = {key: list(values) for key, values in UNIT_ALIASES.items()}
UNITS['bags'] = [u for u in UNITS['bags'] if u != 'packet']
UNITS['bags'] += ['boriya', 'boriyan', 'बोरियां', 'बोरियाँ', 'बोरियां', 'బస్తా', 'బస్తాలు', 'బస్తాల', 'మూటలు', 'மூட்டை', 'மூட்டைகள்', 'சாக்கு', 'ಚೀಲ', 'ಚೀಲಗಳು', 'ಚೀಲಗಳ', 'ചാക്ക്', 'ചാക്കുകൾ', 'पोती', 'पोते', 'বস্তার']
UNITS['kg'] += ['కిలోలు', 'కిలోల', 'கிலோகிராம்', 'ಕಿಲೋ', 'ಕಿಲೋಗ್ರಾಂ', 'किलोग्राम', 'किलोग्रॅम', 'কিলো']
UNITS['litres'] += ['లీటర్లు', 'లీటర్', 'लिटर']
UNITS['boxes'] += ['डिब्बे', 'डिब्बा', 'పెట్టెలు', 'பெட்டிகள்', 'ಪೆಟ್ಟಿಗೆ', 'പെട്ടി', 'বাক্স']
UNITS['pieces'] = [u for u in UNITS['pieces'] if u != 'ടൈം'] + ['units', 'unit', 'नग']
UNITS['dozens'] = [u for u in UNITS['dozens'] if u != 'দশ'] + ['दर्जन', 'డజను', 'ഡസൻ', 'ডজন']
ACTIONS = {key: list(values) for key, values in ACTION_KEYWORDS.items()}
ACTIONS['PURCHASE'] += ['received', 'receive', 'aayi', 'aai', 'jodo', 'आई', 'आए', 'जोड़ो', 'जोड़ें', 'जोड़', 'खरीदा', 'खरीदे', 'खरीदी', 'जोडा', 'आले', 'जोड', 'జోడించు', 'జోడించండి', 'వచ్చాయి', 'కొన్నాను', 'కొను', 'சேர்', 'சேர்க்கவும்', 'வாங்கினேன்', 'வாங்கியது', 'ಸೇರಿಸು', 'ಸೇರಿಸಿ', 'ಬಂದಿದೆ', 'ಖರೀದಿಸಿದೆ', 'ചേർക്കുക', 'ചേർത്തു', 'വാങ്ങി', 'যোগ', 'কিনেছি', 'এলো']
ACTIONS['SALE'] += ['remove', 'deduct', 'बिका', 'बेची', 'बेचे', 'बेचो', 'बेच', 'विकले', 'विकला', 'विका', 'अम्मा', 'అమ్మాను', 'అమ్ము', 'అమ్మండి', 'అమ్మిన', 'అమ్మాము', 'விற்றேன்', 'விற்றது', 'விற்றோம்', 'விற்பனை', 'ಮಾರಾಟ', 'ಮಾರಿದೆ', 'ಮಾರಾಟವಾಯಿತು', 'വിറ്റു', 'വിൽക്കുക', 'বিক্রি', 'বেচেছি']
ACTIONS['DAMAGE'] += ['खराब', 'टूटा', 'నష్టం', 'పాడైంది', 'పాడయ్యాయి', 'சேதம்', 'கெட்டது', 'ಹಾನಿ', 'ಹಾಳಾಗಿದೆ', 'കേടായി', 'കേടുപാട്', 'नुकसान', 'নষ্ট']
ACTIONS['RETURN'] = [a for a in ACTIONS['RETURN'] if a != 'বাড়ি'] + ['वापसी', 'परत', 'వాపసు', 'திரும்ப', 'திருப்பி', 'ವಾಪಸ್', 'മടക്കി', 'തിരികെ', 'ফেরত']
ACTIONS['CREDIT'] += ['అరువు', 'ఉధారం', 'ಸಾಲ', 'കടം', 'ধার']
QUERY = ['how much', 'how many', 'left', 'remaining', 'available', 'show stock', 'check stock', 'where did', 'kitna', 'kitni', 'bacha', 'कितना', 'कितनी', 'बचा', 'बाकी', 'எவ்வளவு', 'மீதம்', 'ఎంత', 'ఎన్ని', 'మిగిలి', 'ಎಷ್ಟು', 'ಉಳಿದಿದೆ', 'എത്ര', 'ബാക്കി', 'किती', 'शिल्लक', 'কত', 'বাকি']
LOW = ['reorder', 'running low', 'what is low', 'what should i buy', 'कम स्टॉक', 'क्या खरीद', 'कौन सा कम', 'kya kam', 'ఏవి తక్కువ', 'ఏమి కొనాలి', 'తక్కువ స్టాక్', 'எதை வாங்க', 'குறைவான', 'ಯಾವುದು ಕಡಿಮೆ', 'ಏನು ಖರೀದಿ', 'എന്ത് വാങ്ങണം', 'കുറവുള്ള', 'काय खरेदी', 'कमी स्टॉक', 'কী কিনব', 'কম স্টক']
NEGATION = ['not', "don't", 'do not', 'never', 'मत', 'नहीं', 'వద్దు', 'வேண்டாம்', 'ಬೇಡ', 'വേണ്ട', 'नको', 'করো না', 'করবেন না']

LOW += ['क्या खरीदना', 'कौन सा स्टॉक कम', 'ఏది తక్కువ', 'என்ன வாங்க', 'काय कमी']

UNITS['packets'] = ['packet', 'packets', 'pack', 'packs', 'पैकेट', 'ప్యాకెట్లు', 'பாக்கெட்', 'ಪ್ಯಾಕೆಟ್', 'പാക്കറ്റ്', 'पॅकेट', 'প্যাকেট']
