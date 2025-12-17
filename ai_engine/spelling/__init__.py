"""
Spelling and Grammar Checker Module.
Supports Uzbek (Latin & Cyrillic) and Russian languages.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SpellingErrorType(Enum):
    """Types of spelling errors."""
    TYPO = "typo"  # Oddiy xato
    MISSING_LETTER = "missing_letter"  # Harf tushib qolgan
    EXTRA_LETTER = "extra_letter"  # Ortiqcha harf
    WRONG_LETTER = "wrong_letter"  # Noto'g'ri harf
    LATIN_CYRILLIC_MIX = "latin_cyrillic_mix"  # Lotin-kirill aralash
    APOSTROPHE = "apostrophe"  # Tutuq belgisi xatosi
    CAPITALIZATION = "capitalization"  # Bosh harf xatosi


@dataclass
class SpellingError:
    """Represents a spelling error."""
    word: str
    suggestion: str
    error_type: SpellingErrorType
    position: int
    line_number: int
    context: str
    language: str
    description: str


class SpellingChecker:
    """
    Spelling checker for Uzbek (Latin & Cyrillic) and Russian.
    """
    
    # Words that should start with 'h' not 'x' (comprehensive list)
    H_WORDS = [
        'hozir', 'hozirgi', 'hozirda', 'hozircha', 'hozirlik',
        'hech', 'hechkim', 'hechqisi', 'hechnarsa', 'hechqaysi', 'hechqanday', 'hechqachon',
        'ham', 'hamda', 'hamkor', 'hamkorlik', 'hamisha', 'hammasi', 'hamma', 'hammamiz',
        'har', 'harakat', 'harakatlar', 'harakatlanish', 'harkatga', 'harqanday', 'harkim',
        'hatto', 'hattoki',
        'holat', 'holati', 'holatda', 'holatlar', 'holatini',
        'hukumat', 'hukumati', 'huqumat',
        'huquq', 'huquqi', 'huquqiy', 'huquqlar', 'huquqlarini', 'huquqshunoslik',
        'hujjat', 'hujjati', 'hujjatlar', 'hujjatlarni', 'hujjatlash',
        'hisob', 'hisobi', 'hisoblab', 'hisoblash', 'hisoblanadi', 'hisoblanish', 'hisobga', 'hisobot',
        'hayot', 'hayoti', 'hayotiy', 'hayotda',
        'his', 'hissiy', 'hissa', 'hissasi',
        'hodisa', 'hodisalar', 'hodisasi',
        'hosil', 'hosili', 'hosilasi', 'hosilot',
        'hurmat', 'hurmati', 'hurmatli',
        'hohish', 'hohishi', 'hohlash',
        'himoya', 'himoyasi', 'himoyalash', 'himoyachi',
        'hikoya', 'hikoyalar', 'hikoyasi',
        'hunarmand', 'hunar', 'hunari',
        'havola', 'havolasi', 'havolalar',
        'havo', 'havosi', 'havoyi',
        'hazil', 'hazilkash',
        'haqiqat', 'haqiqiy', 'haqiqatan',
        'haq', 'haqi', 'haqida', 'haqli', 'haqsiz',
        'halok', 'halokat', 'halol', 'halollik',
        'hammom', 'hammomxona',
        'harbiy', 'harbiylar',
        'hashamat', 'hashamatli',
        'hatto', 'hattoki',
        'havas', 'havasi', 'havaskor', 'havasmand',
        'hayvon', 'hayvonlar', 'hayvonot',
        'hisoblangan', 'hisoblovchi',
        'horigan', 'horijiy', 'hozirjavob',
        'hidoyat', 'hidoyatli',
    ]
    
    # Common Uzbek words with correct spelling (Latin)
    UZBEK_LATIN_DICT = {
        # Legal terms
        'shartnoma', 'kelishuv', 'bitim', 'majburiyat', 'huquq', 'javobgarlik',
        'tomonlar', 'buyurtmachi', 'ijrochi', 'pudratchi', 'yetkazib', 'beruvchi',
        'xizmat', 'narx', 'summa', 'muddat', 'shartlar', 'bandlar', 'qoidalar',
        'nizolar', 'kafolat', 'sifat', 'miqdor', 'hajm', 'umumiy', 'jami',
        
        # Common words
        'aksiyadorlik', 'jamiyati', 'jamiyat', 'korxona', 'tashkilot', 'muassasa',
        'respublika', 'prezident', 'farmoyish', 'qaror', 'buyruq', 'hukumat',
        'vazirlik', 'idora', 'boshqarma', 'rahbar', 'direktor', 'rais',
        
        # Verbs
        'bajarish', 'taqdim', 'etish', 'amalga', 'oshirish', 'joriy', 'qilish',
        'berish', 'olish', 'yetkazish', 'topshirish', 'qabul', 'rad',
        
        # Numbers and dates
        'birinchi', 'ikkinchi', 'uchinchi', 'yanvar', 'fevral', 'mart', 'aprel',
        'may', 'iyun', 'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr',
        
        # Common errors - correct forms
        'hisoblanadi', 'texnologiya', 'texnologiyalar', 'texnologiyalarini',
        'avtomatlashtirish', 'samaradorlik', 'faoliyat', 'loyihalash',
        'ekspluatatsiya', 'qurilish', 'inshoot', 'inshootlar',
        
        # Countries/Places
        "o'zbekiston", 'uzbekistan', 'toshkent', 'samarqand', 'buxoro',
    }
    
    # Common spelling mistakes in Uzbek (wrong -> correct) - expanded
    UZBEK_CORRECTIONS = {
        # X vs H confusion (comprehensive - all forms)
        'xisoblanadi': 'hisoblanadi',
        'xisoblash': 'hisoblash',
        'xisob': 'hisob',
        'xisobi': 'hisobi',
        'xisoblab': 'hisoblab',
        'xisobga': 'hisobga',
        'xisobot': 'hisobot',
        'xech': 'hech',
        'xechkim': 'hechkim',
        'xechnarsa': 'hechnarsa',
        'xechqanday': 'hechqanday',
        'xechqaysi': 'hechqaysi',
        'xechqachon': 'hechqachon',
        'xam': 'ham',
        'xamda': 'hamda',
        'xamkor': 'hamkor',
        'xamkorlik': 'hamkorlik',
        'xamisha': 'hamisha',
        'xamma': 'hamma',
        'xammasi': 'hammasi',
        'xammamiz': 'hammamiz',
        'xar': 'har',
        'xarakat': 'harakat',
        'xarakatlar': 'harakatlar',
        'xarqanday': 'harqanday',
        'xarkim': 'harkim',
        'xatto': 'hatto',
        'xattoki': 'hattoki',
        'xozir': 'hozir',
        'xozirgi': 'hozirgi',
        'xozirda': 'hozirda',
        'xozircha': 'hozircha',
        'xozirlik': 'hozirlik',
        'xolat': 'holat',
        'xolati': 'holati',
        'xolatda': 'holatda',
        'xolatlar': 'holatlar',
        'xukumat': 'hukumat',
        'xukumati': 'hukumati',
        'xuquq': 'huquq',
        'xuquqi': 'huquqi',
        'xuquqiy': 'huquqiy',
        'xuquqlar': 'huquqlar',
        'xujjat': 'hujjat',
        'xujjati': 'hujjati',
        'xujjatlar': 'hujjatlar',
        'xujjatlash': 'hujjatlash',
        'xayot': 'hayot',
        'xayoti': 'hayoti',
        'xayotiy': 'hayotiy',
        'xis': 'his',
        'xissiy': 'hissiy',
        'xissa': 'hissa',
        'xodisa': 'hodisa',
        'xodisalar': 'hodisalar',
        'xosil': 'hosil',
        'xosili': 'hosili',
        'xurmat': 'hurmat',
        'xurmati': 'hurmati',
        'xurmatli': 'hurmatli',
        'xoxish': 'hohish',
        'xoxishi': 'hohishi',
        'ximoya': 'himoya',
        'ximoyasi': 'himoyasi',
        'xikoya': 'hikoya',
        'xikoyalar': 'hikoyalar',
        'xunarmand': 'hunarmand',
        'xunar': 'hunar',
        'xavola': 'havola',
        'xavolasi': 'havolasi',
        'xavo': 'havo',
        'xavosi': 'havosi',
        'xazil': 'hazil',
        'xaqiqat': 'haqiqat',
        'xaqiqiy': 'haqiqiy',
        'xaq': 'haq',
        'xaqi': 'haqi',
        'xaqida': 'haqida',
        'xaqli': 'haqli',
        'xalok': 'halok',
        'xalokat': 'halokat',
        'xalol': 'halol',
        'xammom': 'hammom',
        'xarbiy': 'harbiy',
        'xashamat': 'hashamat',
        'xavas': 'havas',
        'xavasi': 'havasi',
        'xayvon': 'hayvon',
        'xayvonlar': 'hayvonlar',
        'xorijiy': 'horijiy',
        
        # Boshqa X→H xatolar
        'xamma': 'hamma',
        'xammasi': 'hammasi',
        'xabar': 'habar',
        'xafsizlik': 'xavfsizlik',
        'xaqorat': 'haqorat',
        'xayriya': 'hayriya',
        'xayrli': 'hayrli',
        
        # Double letters
        'jammiyati': 'jamiyati',
        'jammiyat': 'jamiyat',
        'kelisshuv': 'kelishuv',
        'sharttoma': 'shartnoma',
        'majjburiyat': 'majburiyat',
        'qonunn': 'qonun',
        'bosshliq': 'boshlik',
        'ishshi': 'ishi',
        'yilllik': 'yillik',
        
        # Missing letters
        'uzbekstan': 'uzbekiston',
        "o'zbekstan": "o'zbekiston",
        'texnlogiya': 'texnologiya',
        'texnlogiyalar': 'texnologiyalar',
        'texnlogiyalarini': 'texnologiyalarini',
        'avtmatlash': 'avtomatlashtirish',
        'samradorlik': 'samaradorlik',
        'faoliyti': 'faoliyati',
        'loyihlash': 'loyihalash',
        'qonunchilik': 'qonunchilik',
        'boshqrma': 'boshqarma',
        'korxna': 'korxona',
        'tashkilt': 'tashkilot',
        
        # Wrong letters
        'sharnoma': 'shartnoma',
        'majburiat': 'majburiyat',
        'javobgrlik': 'javobgarlik',
        'buyurtmachy': 'buyurtmachi',
        'ijrochy': 'ijrochi',
        'beruvchy': 'beruvchi',
        
        # Common typos and misspellings
        'yoq': "yo'q",
        'yok': "yo'q",
        
        # Qanday variants
        'qaley': 'qanday',
        'qalay': 'qanday',
        'qandey': 'qanday',
        'qanaqa': 'qanday',
        
        # Bilan variants
        'blan': 'bilan',
        'bln': 'bilan',
        'biln': 'bilan',
        'bila': 'bilan',
        
        # Lekin variants
        'lekn': 'lekin',
        'lekni': 'lekin',
        'lakn': 'lekin',
        'lakin': 'lekin',
        
        # Keyin variants
        'keyn': 'keyin',
        'keyni': 'keyin',
        'kein': 'keyin',
        
        # Uchun variants
        'uchn': 'uchun',
        'uchн': 'uchun',
        'uchu': 'uchun',
        
        # Qilish variants
        'qilsh': 'qilish',
        'qilih': 'qilish',
        'qilis': 'qilish',
        
        # Borish variants
        'borsh': 'borish',
        'borsih': 'borish',
        
        # Kelish variants
        'kelsh': 'kelish',
        'kelsih': 'kelish',
        
        # Olish variants
        'olsh': 'olish',
        'olsih': 'olish',
        
        # Berish variants
        'bersh': 'berish',
        'bersih': 'berish',
        
        # Nima variants
        'nimа': 'nima',
        'nma': 'nima',
        'nimaa': 'nima',
        
        # Qayerda variants
        'qayerda': 'qayerda',
        'qayrda': 'qayerda',
        'qayerda': 'qayerda',
        
        # Qachon variants
        'qachn': 'qachon',
        'qachоn': 'qachon',
        
        # Men variants
        'mеn': 'men',
        'mn': 'men',
        
        # Sen variants
        'sеn': 'sen',
        'sn': 'sen',
        
        # Siz variants
        'sіz': 'siz',
        'sz': 'siz',
        
        # Ular variants
        'ulаr': 'ular',
        'ulr': 'ular',
        
        # Biz variants
        'bіz': 'biz',
        'bz': 'biz',
        
        # Edi variants
        'еdi': 'edi',
        'ed': 'edi',
        
        # Emas variants
        'emаs': 'emas',
        'ems': 'emas',
        
        # Shunday variants
        'shundy': 'shunday',
        'shundey': 'shunday',
        'shunay': 'shunday',
        
        # Bunday variants  
        'bundy': 'bunday',
        'bundey': 'bunday',
        'bunay': 'bunday',
        
        # Albatta variants
        'albata': 'albatta',
        'albatda': 'albatta',
        'albbata': 'albatta',
        
        # Balki variants
        'balkі': 'balki',
        'blki': 'balki',
        
        # Chunki variants
        'chunki': 'chunki',
        'chnki': 'chunki',
        'chunka': 'chunki',
        
        # Shuning variants
        'shunig': 'shuning',
        'shunng': 'shuning',
        
        # Va variants
        'vа': 'va',
        
        # Yoki variants
        'yokі': 'yoki',
        'yok': "yo'q",
        
        # Agar variants
        'agаr': 'agar',
        'agr': 'agar',
        
        # Bormi variants
        'bormі': 'bormi',
        'borm': 'bormi',
        
        # Kerak variants
        'kerk': 'kerak',
        'kerаk': 'kerak',
        
        # Mumkin variants
        'mumkn': 'mumkin',
        'mumkіn': 'mumkin',
        
        # Zarur variants
        'zarr': 'zarur',
        'zаrur': 'zarur',
        
        # Yaxshi variants
        'yaxhi': 'yaxshi',
        'yahshi': 'yaxshi',
        'yaxsi': 'yaxshi',
        
        # Yomon variants
        'yomn': 'yomon',
        'yomоn': 'yomon',
        
        # Katta variants
        'kata': 'katta',
        'katа': 'katta',
        
        # Kichik variants
        'kichk': 'kichik',
        'kichіk': 'kichik',
        
        # Q vs G confusion
        'garb': 'g\'arb',
        'garbiy': 'g\'arbiy',
        'ogir': "og'ir",
        'ogirlik': "og'irlik",
        'togri': "to'g'ri",
        'togrilab': "to'g'rilab",
        
        # Apostrophe issues (backtick ` instead of apostrophe ')
        "o`zbekiston": "o'zbekiston",
        "ko`prik": "ko'prik",
        "ko`prikqurilish": "ko'prikqurilish",
        "bo`lim": "bo'lim",
        "to`lov": "to'lov",
        "qo`shimcha": "qo'shimcha",
        "ma`lumot": "ma'lumot",
        "ta`minlash": "ta'minlash",
        "bo`yicha": "bo'yicha",
        "ko`rsatish": "ko'rsatish",
        "ko`chasi": "ko'chasi",
        "bog`iston": "bog'iston",
        "o`rniga": "o'rniga",
        "yo`l": "yo'l",
        "so`z": "so'z",
        "to`g`ri": "to'g'ri",
        "qo`l": "qo'l",
        "o`qish": "o'qish",
        "o`rganish": "o'rganish",
        "mo`ljal": "mo'ljal",
        "ko`p": "ko'p",
        "bo`sh": "bo'sh",
        "so`m": "so'm",
        "o`z": "o'z",
        "yo`q": "yo'q",
        "bo`ladi": "bo'ladi",
        "ko`rinish": "ko'rinish",
        "qo`shni": "qo'shni",
        "to`plam": "to'plam",
        "o`tkazgich": "o'tkazgich",
        "g`arb": "g'arb",
        "g`arbiy": "g'arbiy",
        "og`ir": "og'ir",
        "to`g`ri": "to'g'ri",
        
        # IT terms
        'dasturiy': "dasturiy",
        'texnologiya': 'texnologiya',
        'kompyuter': 'kompyuter',
        'internet': 'internet',
        'websayt': 'veb-sayt',
        'dasturchi': "dasturchi",
    }
    
    # Russian common corrections
    RUSSIAN_CORRECTIONS = {
        'даговор': 'договор',
        'обязательсво': 'обязательство',
        'ответственость': 'ответственность',
        'выполение': 'выполнение',
        'предоставение': 'предоставление',
        'соглашенние': 'соглашение',
        'обеспеченние': 'обеспечение',
        'исполнене': 'исполнение',
        'услуга': 'услуга',
        'оплата': 'оплата',
        'стоимоть': 'стоимость',
        'качесво': 'качество',
        'гарантя': 'гарантия',
    }
    
    # Cyrillic letters that look like Latin (commonly confused)
    CYRILLIC_LATIN_SIMILAR = {
        'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y',
        'х': 'x', 'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M',
        'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X',
    }
    
    def __init__(self):
        """Initialize the spelling checker."""
        # Build reverse lookup for suggestions
        self.all_corrections = {
            **self.UZBEK_CORRECTIONS,
            **self.RUSSIAN_CORRECTIONS
        }
    
    def check_text(self, text: str, language: str = 'uz-latn') -> List[SpellingError]:
        """
        Check text for spelling errors.
        
        Args:
            text: Text to check
            language: Language code ('uz-latn', 'uz-cyrl', 'ru')
            
        Returns:
            List of SpellingError objects
        """
        errors = []
        seen_errors = set()

        def emit_error(word: str, suggestion: str, error_type: SpellingErrorType, position: int,
                       line_number: int, context: str, language: str, description: str) -> bool:
            """Append the error unless we already reported this occurrence."""
            key = (line_number, position, word.lower(), error_type, suggestion.lower())
            if key in seen_errors:
                return False
            seen_errors.add(key)
            errors.append(SpellingError(
                word=word,
                suggestion=suggestion,
                error_type=error_type,
                position=position,
                line_number=line_number,
                context=context,
                language=language,
                description=description
            ))
            return True
        
        # Split into lines for line number tracking
        lines = text.split('\n')
        
        position = 0
        for line_num, line in enumerate(lines, 1):
            # Find words in line
            words = self._extract_words(line)
            
            for word, word_pos in words:
                word_lower = word.lower()
                error_found = False
                position_index = position + word_pos
                context = self._get_context(line, word_pos, word)
                
                # 1. Check for known misspellings first
                if word_lower in self.all_corrections:
                    correction = self.all_corrections[word_lower]
                    # Preserve original case
                    if word.isupper():
                        correction = correction.upper()
                    elif word[0].isupper():
                        correction = correction.capitalize()
                    
                    error_type = self._determine_error_type(word_lower, correction)
                    
                    emit_error(
                        word=word,
                        suggestion=correction,
                        error_type=error_type,
                        position=position_index,
                        line_number=line_num,
                        context=context,
                        language=language,
                        description=self._get_error_description(error_type, word, correction)
                    )
                    error_found = True
                
                # 2. Auto-detect x -> h errors using comprehensive H_WORDS list
                if not error_found and word_lower.startswith('x') and len(word_lower) > 1:
                    potential_h = 'h' + word_lower[1:]
                    if potential_h in self.H_WORDS:
                        correction = 'h' + word[1:]  # Preserve case
                        if word.isupper():
                            correction = correction.upper()
                        elif word[0].isupper():
                            correction = 'H' + word[1:].lower()
                        
                        emit_error(
                            word=word,
                            suggestion=correction,
                            error_type=SpellingErrorType.WRONG_LETTER,
                            position=position_index,
                            line_number=line_num,
                            context=context,
                            language=language,
                            description=f"'x' o'rniga 'h' bo'lishi kerak: '{word}' → '{correction}'"
                        )
                        error_found = True
                
                # 3. Check for backtick (`) instead of apostrophe (') in the middle of a word
                if not error_found and self._has_internal_backtick(word):
                    suggestion = word.replace('`', "'")
                    emit_error(
                        word=word,
                        suggestion=suggestion,
                        error_type=SpellingErrorType.APOSTROPHE,
                        position=position_index,
                        line_number=line_num,
                        context=context,
                        language='uz-latn',
                        description=f"Tutuq belgisi noto'g'ri: '`' o'rniga "'" ishlatilishi kerak"
                    )
                    error_found = True
                
                # 4. Check for missing apostrophe in common words
                if not error_found:
                    apostrophe_words = {
                        'ozbekiston': "o'zbekiston",
                        'koprik': "ko'prik",
                        'bolim': "bo'lim",
                        'tolov': "to'lov",
                        'qoshimcha': "qo'shimcha",
                        'malumot': "ma'lumot",
                        'taminlash': "ta'minlash",
                        'boyicha': "bo'yicha",
                        'korsatish': "ko'rsatish",
                        'kochasi': "ko'chasi",
                        'orniga': "o'rniga",
                        'yol': "yo'l",
                        'soz': "so'z",
                        'togri': "to'g'ri",
                        'qol': "qo'l",
                        'oqish': "o'qish",
                        'organish': "o'rganish",
                        'moljal': "mo'ljal",
                        'kop': "ko'p",
                        'bosh': "bo'sh",
                        'som': "so'm",
                        'oz': "o'z",
                        'yoq': "yo'q",
                        'boladi': "bo'ladi",
                        'korinish': "ko'rinish",
                        'qoshni': "qo'shni",
                        'toplam': "to'plam",
                        'garb': "g'arb",
                        'garbiy': "g'arbiy",
                        'ogir': "og'ir",
                        'bolib': "bo'lib",
                        'bolgan': "bo'lgan",
                        'bolsa': "bo'lsa",
                        'bolishi': "bo'lishi",
                        'korib': "ko'rib",
                        'korish': "ko'rish",
                        'kora': "ko'ra",
                        'qolib': "qo'lib",
                        'qoya': "qo'ya",
                        'tomon': "to'mon",
                        'topon': "to'pon",
                        'yoriq': "yo'riq",
                        'yoriqnoma': "yo'riqnoma",
                    }
                    if word_lower in apostrophe_words:
                        suggestion = apostrophe_words[word_lower]
                        if word.isupper():
                            suggestion = suggestion.upper()
                        elif word[0].isupper():
                            suggestion = suggestion.capitalize()
                        
                        emit_error(
                            word=word,
                            suggestion=suggestion,
                            error_type=SpellingErrorType.APOSTROPHE,
                            position=position_index,
                            line_number=line_num,
                            context=context,
                            language='uz-latn',
                            description=f"Tutuq belgisi tushib qolgan: '{word}' → '{suggestion}'"
                        )
                        error_found = True
                
                # 5. Check for mixed Latin/Cyrillic
                if not error_found:
                    mixed_error = self._check_mixed_script(word, line_num, position + word_pos, line, word_pos)
                    if mixed_error:
                        errors.append(mixed_error)
            
            position += len(line) + 1  # +1 for newline
        
        return errors
    
    def _extract_words(self, line: str) -> List[Tuple[str, int]]:
        """Extract words with their positions from a line."""
        words = []
        # Match words including apostrophes and special Uzbek characters
        pattern = r"[a-zA-Zа-яА-ЯёЁўғқҳҚҒҲЎ'`']+(?:'[a-zA-Zа-яА-ЯёЁ]+)?"
        
        for match in re.finditer(pattern, line):
            words.append((match.group(), match.start()))
        
        return words
    
    def _determine_error_type(self, wrong: str, correct: str) -> SpellingErrorType:
        """Determine the type of spelling error."""
        if len(wrong) > len(correct):
            return SpellingErrorType.EXTRA_LETTER
        elif len(wrong) < len(correct):
            return SpellingErrorType.MISSING_LETTER
        else:
            return SpellingErrorType.WRONG_LETTER
    
    def _check_mixed_script(self, word: str, line_num: int, position: int, 
                           line: str, word_pos: int) -> Optional[SpellingError]:
        """Check for mixed Latin/Cyrillic characters in a word."""
        has_latin = bool(re.search(r'[a-zA-Z]', word))
        has_cyrillic = bool(re.search(r'[а-яА-ЯёЁ]', word))
        
        if has_latin and has_cyrillic:
            # Try to suggest correction
            suggestion = self._fix_mixed_script(word)
            
            return SpellingError(
                word=word,
                suggestion=suggestion,
                error_type=SpellingErrorType.LATIN_CYRILLIC_MIX,
                position=position,
                line_number=line_num,
                context=self._get_context(line, word_pos, word),
                language='mixed',
                description=f"So'zda lotin va kirill harflari aralashgan: '{word}'"
            )
        
        return None
    
    def _fix_mixed_script(self, word: str) -> str:
        """Try to fix mixed script word."""
        # Count Latin vs Cyrillic
        latin_count = len(re.findall(r'[a-zA-Z]', word))
        cyrillic_count = len(re.findall(r'[а-яА-ЯёЁ]', word))
        
        result = word
        
        if latin_count > cyrillic_count:
            # Convert Cyrillic lookalikes to Latin
            for cyr, lat in self.CYRILLIC_LATIN_SIMILAR.items():
                result = result.replace(cyr, lat)
        else:
            # Convert Latin lookalikes to Cyrillic
            lat_to_cyr = {v: k for k, v in self.CYRILLIC_LATIN_SIMILAR.items()}
            for lat, cyr in lat_to_cyr.items():
                result = result.replace(lat, cyr)
        
        return result

    def _has_internal_backtick(self, word: str) -> bool:
        """Return True if the word contains a backtick between letters."""
        for idx, char in enumerate(word):
            if char == '`' and 0 < idx < len(word) - 1:
                if word[idx - 1].isalpha() and word[idx + 1].isalpha():
                    return True
        return False
    
    def _check_apostrophe(self, word: str, line_num: int, position: int,
                         line: str, word_pos: int) -> Optional[SpellingError]:
        """Check for incorrect apostrophe usage in Uzbek."""
        # Check for backtick instead of apostrophe
        if self._has_internal_backtick(word):
            suggestion = word.replace('`', "'")
            return SpellingError(
                word=word,
                suggestion=suggestion,
                error_type=SpellingErrorType.APOSTROPHE,
                position=position,
                line_number=line_num,
                context=self._get_context(line, word_pos, word),
                language='uz-latn',
                description=f"Tutuq belgisi noto'g'ri: '`' o'rniga \"'\" ishlatilishi kerak"
            )
        
        return None
    
    def _get_context(self, line: str, word_pos: int, word: str, context_size: int = 30) -> str:
        """Get context around the word."""
        start = max(0, word_pos - context_size)
        end = min(len(line), word_pos + len(word) + context_size)
        
        context = line[start:end]
        if start > 0:
            context = "..." + context
        if end < len(line):
            context = context + "..."
        
        return context
    
    def _get_error_description(self, error_type: SpellingErrorType, 
                               wrong: str, correct: str) -> str:
        """Get human-readable error description."""
        descriptions = {
            SpellingErrorType.TYPO: f"Imloviy xato: '{wrong}' → '{correct}'",
            SpellingErrorType.MISSING_LETTER: f"Harf tushib qolgan: '{wrong}' → '{correct}'",
            SpellingErrorType.EXTRA_LETTER: f"Ortiqcha harf: '{wrong}' → '{correct}'",
            SpellingErrorType.WRONG_LETTER: f"Noto'g'ri harf: '{wrong}' → '{correct}'",
            SpellingErrorType.LATIN_CYRILLIC_MIX: f"Lotin-kirill aralash: '{wrong}'",
            SpellingErrorType.APOSTROPHE: f"Tutuq belgisi xatosi: '{wrong}'",
            SpellingErrorType.CAPITALIZATION: f"Bosh harf xatosi: '{wrong}' → '{correct}'",
        }
        return descriptions.get(error_type, f"Imloviy xato: '{wrong}' → '{correct}'")
    
    def get_summary(self, errors: List[SpellingError]) -> Dict:
        """Get summary of spelling errors."""
        if not errors:
            return {
                'total_errors': 0,
                'by_type': {},
                'by_language': {},
                'unique_errors': 0,
            }
        
        by_type = {}
        by_language = {}
        unique_words = set()
        
        for error in errors:
            # Count by type
            type_name = error.error_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            
            # Count by language
            by_language[error.language] = by_language.get(error.language, 0) + 1
            
            # Track unique words
            unique_words.add(error.word.lower())
        
        return {
            'total_errors': len(errors),
            'by_type': by_type,
            'by_language': by_language,
            'unique_errors': len(unique_words),
        }


# Export
__all__ = ['SpellingChecker', 'SpellingError', 'SpellingErrorType']
