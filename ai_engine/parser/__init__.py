"""
Contract Parser Module.
Parses contract text and extracts structured sections and clauses.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from .inn_registry import resolve_inn_name

logger = logging.getLogger(__name__)


class SectionType(Enum):
    """Contract section types."""
    HEADER = "header"
    PARTIES = "parties"
    SUBJECT = "subject"
    RIGHTS = "rights"
    OBLIGATIONS = "obligations"
    PRICE = "price"
    DELIVERY = "delivery"
    QUALITY = "quality"
    WARRANTY = "warranty"
    LIABILITY = "liability"
    FORCE_MAJEURE = "force_majeure"
    DISPUTE = "dispute"
    TERM = "term"
    TERMINATION = "termination"
    CONFIDENTIAL = "confidential"
    ADDITIONAL = "additional"
    REQUISITES = "requisites"
    SIGNATURES = "signatures"
    OTHER = "other"


@dataclass
class Clause:
    """Represents a single clause in a contract."""
    number: str
    content: str
    section_type: SectionType
    start_pos: int
    end_pos: int


@dataclass
class Section:
    """Represents a section of a contract."""
    section_type: SectionType
    title: str
    number: str
    content: str
    clauses: List[Clause] = field(default_factory=list)
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class ContractMetadata:
    """Extracted contract metadata."""
    contract_number: Optional[str] = None
    contract_date: Optional[str] = None
    contract_type: Optional[str] = None
    party_a_name: Optional[str] = None
    party_a_inn: Optional[str] = None
    party_a_address: Optional[str] = None
    party_b_name: Optional[str] = None
    party_b_inn: Optional[str] = None
    party_b_address: Optional[str] = None
    total_amount: Optional[str] = None
    currency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    language: str = "uz-latn"


class ContractParser:
    """
    Parser for Uzbek contracts.
    Extracts sections, clauses, and metadata from contract text.
    """
    
    # Section header patterns (Uzbek and Russian)
    SECTION_PATTERNS = {
        SectionType.SUBJECT: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:SHARTNOMA\s+PREDMETI|Shartnoma\s+mavzusi)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:PREDMET|MAVZU|SHARTNOMA\s+MAVZUSI)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ПРЕДМЕТ\s+ДОГОВОРА|ШАРТНОМА\s+ПРЕДМЕТИ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ШАРТНОМА\s+МАВЗУСИ|МАВЗУ)",
            r"(?i)(?:^|\n)\s*(?:Мавзуси)",
            r"(?i)(?:^|\n)\s*(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]?\s*(?:\n\s*)?(?:ШАРТНОМА\s+ПРЕДМЕТИ|ШАРТНОМА\s+МАВЗУСИ)",
        ],
        SectionType.PARTIES: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:TOMONLAR|СТОРОНЫ|Taraflar)",
            r"(?i)bir\s+tomondan.*boshqa\s+tomondan",
            r"(?i)с\s+одной\s+стороны.*с\s+другой\s+стороны",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ТОМОНЛАР|Тарафлар)",
            r"(?i)бир\s+томондан.*иккинчи\s+томондан",
        ],
        SectionType.RIGHTS: [
            r"(?i)(?:^|\n)\s*(?:(?:\d+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:TOMONLARNING\s+HUQUQLARI|ПРАВА\s+СТОРОН|Huquqlar)",
            r"(?i)(?:^|\n)\s*(?:(?:\d+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ҲУҚУҚЛАР|Ҳуқуқлар)",
        ],
        SectionType.OBLIGATIONS: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:TOMONLARNING\s+MAJBURIYATLARI|ОБЯЗАННОСТИ\s+СТОРОН|Majburiyatlar)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:HUQUQ\s+VA\s+MAJBURIYATLAR|ПРАВА\s+И\s+ОБЯЗАННОСТИ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:МАЖБУРИЯТЛАР|Мажбуриятлар|ҲУҚУҚ\s+ВА\s+МАЖБУРИЯТЛАР)",
        ],
        SectionType.PRICE: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:SHARTNOMA\s+NARXI|Shartnoma\s+narxi)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:NARX\s+VA\s+TO['']LOV|QIYMAT|ISHLAR\s+QIYMATI)",
            r"(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ЦЕНА\s+ДОГОВОРА|ЦЕНА\s+И\s+ПОРЯДОК\s+РАСЧЕТОВ|СТОИМОСТЬ)",
            r"(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ПОРЯДОК\s+ОПЛАТЫ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ШАРТНОМА\s+БЎЙИЧА\s+ИШЛАР\s+ҚИЙМАТИ|ИШЛАР\s+ҚИЙМАТИ|ШАРТНОМА\s+НАРХИ|НАРХ\s+ВА\s+ТЎЛОВ|ТЎЛОВ\s+ТАРТИБИ|ТЎЛОВЛАР\s+ВА\s+ҲИСОБ-КИТОБЛАР|СТОИМОСТЬ\s+РАБОТ|ШАРТНОМАНИНГ\s+БАҲОСИ\s+ВА\s+ҲИСОБ-КИТОБ\s+ТАРТИБИ)",
            r"(?i)(?:^|\n)\s*(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]?\s*(?:\n\s*)?(?:ШАРТНОМАНИНГ\s+БАҲОСИ\s+ВА\s+ҲИСОБ-КИТОБ\s+ТАРТИБИ)",
        ],
        SectionType.DELIVERY: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:YETKAZIB\s+BERISH|ПОСТАВКА|ДОСТАВКА)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:TOPSHIRISH\s+TARTIBI|ПОРЯДОК\s+СДАЧИ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ЕТКАЗИБ\s+БЕРИШ|ТОПШИРИШ\s+ТАРТИБИ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:СРОКИ\s+И\s+ПОРЯДОК\s+ПОСТАВК\w*)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ПОРЯДОК\s+ПРИ[ЁЕ]М\w*\s*ПЕРЕДАЧ\w*\s*ТОВАР\w*)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ПРИ[ЁЕ]МКА\s*И\s*ПЕРЕДАЧ\w*)",
        ],
        SectionType.QUALITY: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:SIFAT\s+TALABLARI|ТРЕБОВАНИЯ\s+К\s+КАЧЕСТВУ|Sifat)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:СИФАТ\s+ТАЛАБЛАРИ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:КАЧЕСТВО\s+И\s+КОЛИЧЕСТВО\s+ПРОДУКЦИИ)",
        ],
        SectionType.WARRANTY: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:KAFOLAT|ГАРАНТИЯ|ГАРАНТИЙНЫЕ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:КАФОЛАТ)",
        ],
        SectionType.LIABILITY: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:JAVOBGARLIK|ОТВЕТСТВЕННОСТЬ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:MODDIY\s+JAVOBGARLIK|МАТЕРИАЛЬНАЯ\s+ОТВЕТСТВЕННОСТЬ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ЖАВОБГАРЛИК)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ОТВЕТСТВЕННОСТЬ\s+СТОРОН|ТОМОНЛАРНИНГ\s+ЖАВОБГАРЛИГИ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVXХ]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:МУЛКИЙ\s+ЖАВОБГАРЛИГИ|ТОМОНЛАРНИНГ\s+МУЛКИЙ\s+ЖАВОБГАРЛИГИ)",
        ],
        SectionType.FORCE_MAJEURE: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:FORS-MAJOR|ФОРС-МАЖОР|Favqulodda\s+holatlar)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ФОРС-МАЖОР)",
        ],
        SectionType.DISPUTE: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:NIZOLARNI\s+HAL\s+QILISH|РАЗРЕШЕНИЕ\s+СПОРОВ|Nizolar)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:НИЗОЛАРНИ\s+ҲАЛ\s+ҚИЛИШ|НИЗОЛАР)",
        ],
        SectionType.TERM: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:SHARTNOMA\s+MUDDATI|СРОК\s+ДЕЙСТВИЯ|СРОК\s+ДОГОВОРА)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:AMAL\s+QILISH\s+MUDDATI|MUDDATI)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ШАРТНОМА\s+МУДДАТИ|АМАЛ\s+ҚИЛИШ\s+МУДДАТИ|ШАРТНОМАНИНГ\s+АМАЛ\s+ҚИЛИШИ|ИШЛАРНИ\s+БАЖАРИШ\s+МУДДАТЛАРИ|СРОКИ\s+ВЫПОЛНЕНИЯ\s+РАБОТ)",
            r"(?i)(?:ШАРТНОМАНИНГ\s+АМАЛ\s+КИЛИШ\s+МУДДАТИ|АМАЛ\s+КИЛИШ\s+МУДДАТИ)",
            r"(?i)(?:amal\s+qiladi|действует|срок|amал\s+kili?sh\s+muddat[iy])",
        ],
        SectionType.TERMINATION: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:SHARTNOMANI\s+BEKOR\s+QILISH|РАСТОРЖЕНИЕ\s+ДОГОВОРА)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ШАРТНОМАНИ\s+БЕКОР\s+ҚИЛИШ)",
        ],
        SectionType.CONFIDENTIAL: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:MAXFIYLIK|КОНФИДЕНЦИАЛЬНОСТЬ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:МАХФИЙЛИК)",
        ],
        SectionType.ADDITIONAL: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:QO['']SHIMCHA\s+SHARTLAR|ДОПОЛНИТЕЛЬНЫЕ\s+УСЛОВИЯ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:BOSHQA\s+SHARTLAR|ПРОЧИЕ\s+УСЛОВИЯ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:YAKUNIY\s+QOIDALAR|ЗАКЛЮЧИТЕЛЬНЫЕ\s+ПОЛОЖЕНИЯ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ҚЎШИМЧА\s+ШАРТЛАР|БОШҚА\s+ШАРТЛАР|ЯКУНИЙ\s+ҚОИДАЛАР)",
        ],
        SectionType.REQUISITES: [
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:TOMONLARNING\s+REKVIZITLARI|РЕКВИЗИТЫ\s+СТОРОН)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:YURIDIK\s+MANZILLAR|ЮРИДИЧЕСКИЕ\s+АДРЕСА)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ТОМОНЛАРНИНГ\s+РЕКВИЗИТЛАРИ|ЮРИДИК\s+МАНЗИЛЛАР)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:REKVIZIT|РЕКВИЗИТ)",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:ЮРИДИЧЕСКИЕ\s+АДРЕСА\s+И\s+РЕКВИЗИТЫ\s+СТОРОН)",
            r"(?i)(?:^|\n)\s*(?:Исполнитель|Заказчик)\s*[:–—]",
            r"(?i)(?:^|\n)\s*(?:(?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*)?(?:БАНК\s+РЕКВИЗИТЛАРИ)",
        ],
        SectionType.SIGNATURES: [
            r"(?i)(?:^|\n)\s*(?:IMZOLAR|ПОДПИСИ\s+СТОРОН)",
            r"(?i)M\.O['']\..*M\.O['']",  # M.O'. pattern for stamps
            r"(?i)(?:^|\n)\s*(?:ИМЗОЛАР)",
        ],
    }
    
    # Metadata extraction patterns
    METADATA_PATTERNS = {
        'contract_number': [
            # First line header: "ШАРТНОМA No 10 (...)" or blank with number elsewhere
            r"(?im)^[^\n]{0,80}ШАРТНОМАСИ\s+([0-9A-Za-z\-/]{1,20})",
            r"(?im)^\s*(?:ШАРТНОМA|ШАРТНОМА|SHARTNOMA|ДОГОВОР|CONTRACT)\s+(?:№|No|N)\.?\s*([\d\-/\А-Я]+)",
            # Generic patterns with raqami/номер keywords
            r"(?i)(?:shartnoma|договор|шартнома)\s*(?:raqami|номер|№|No|N|#)\s*([\d\А-Я\-/]+)",
            # Standalone number markers
            r"(?i)№\s*([A-Za-z0-9\-/]+)",
            r"(?i)shartnoma\s*№?\s*([A-Za-z0-9\-/]+)",
            r"(?i)договор\s*№?\s*([A-Za-z0-9\-/]+)",
            # "number-sonli" pattern (Uzbek)
            r"(?i)\b([A-Za-z0-9\-/]+)\b\s*(?:–|-)?\s*сонли",
            # Search in requisites section
            r"(?im)(?:shartnoma|договор|шартнома).*?(?:raqami|номер|№|No)\s*[:–—-]?\s*([0-9\-/]+)",
        ],
        'contract_date': [
            r"(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})",
            r"(\d{1,2})\s+(yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|oktabr|noyabr|dekabr|октябр|сентябр|август|июль|июнь|май|апрель|март|февраль|январь|ноябрь|октябрь|декабрь)\s+(\d{4})",
            r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})",
            r"(?i)(?:shartnoma|договор|дата)\s+(?:sanasi|санаси)?\s*[:=]?\s*(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})",
            r"(?i)(?:shartnoma|договор)\s+raqami.*?(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})",
            r"(?i)ш\.\s*\".*?(\d{1,2})\s*(yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|oktabr|noyabr|dekabr)\s+(\d{4})",
            r"(\d{1,2})\s+(yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|oktabr|noyabr|dekabr)(?:i|da|дагі|дага|дам|дайн)\s+(\d{4})",  # Uzbek suffix forms
        ],
        'inn': [
            r"(?i)(?:INN|ИНН|STIR)[\s:–-]*(\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d)",  # INN label: must have 9 digits
            r"(?i)(?:ШХ|МФО)[\s:]*(\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d)",  # Uzbek STIR format (ШХ)
            r"(\d{9})",  # Standalone 9-digit numbers (as fallback in requisites)
        ],
        'amount': [
            # Numeric with three groups and optional decimals, tolerant to missing currency markers
            r"(?i)(\d{1,3}(?:\s\d{3}){2}(?:[\.,]\d{2})?)\s*(?:\([^)]*\))?\s*(?:сумни|сум|сўм|uzs|usd|eur|rub|кк,?с|ққс)?",
            # Uzbek Cyrillic with detailed amount format
            r"(?i)(?:шартноманинг|шартнома\s+буйича\s+(?:ишлар\s+)?|ишлар\s+)?(?:умумий\s+)?(?:қиймати|киймати|нарх[и]?)\s*(?:таҳминий\s+)?(?:ққс\s+билан\s+)?([\d\s]{10,})",
            # Uzbek with units
            r"(?i)(?:шартнома\s+буйича\s+(?:ишлар\s+)?киймати|киймати|нарх[и]?)\s*(?:барча\s+соликлар[,\s]*)?[\s]*(\d[\d\s]+)\s*(?:сум|сўм|UZS|USD|EUR|RUB)",
            r"(?i)(?:шартнома\s+буйича\s+ишлар|ишлар\s+қиймати|қиймати|нарх[и]?)\s*[\s]*(\d[\d\s]+)\s*(?:сумни|сум|сўм|UZS|USD|EUR|RUB)",
            # Standalone formatted numbers with currency
            r"(?i)(\d{1,3}[\s]+\d{3}[\s]+\d{3}[\s]+\d{3})\s*(?:сумни|сумлик|\(|сум|сўм|млн\s+сўм|млрд\s+сўм)",
            r"(?i)(\d{1,3}[\s]*(?:\d{3}[\s]*)*(?:\d{1,3})?)\s*(?:млрд\s+(?:сўм|сум)|млн\s+(?:сўм|сум))",
            r"(?i)(\d{1,3}[\s]*(?:\d{3}[\s]*)*(?:\d{1,3})?)\s*(?:so['']m|so[''`]?m|сум|сўм|UZS|USD|EUR|RUB|₽|\$)",
            # Common abbreviations
            r"(?i)jami\s*[:=]?\s*(\d[\d\s]*[\.,]?\d*)",
            r"(?i)(?:umumiy\s+qiymati|jami\s+qiymati|to\'liq\s+qiymati)\s*[:=—-]?\s*(\d[\d\s\.,]*\d?)",
            r"(?i)(?:итого|Итого)\s*[:=]?\s*(\d[\d\s]*[\.,]?\d*)",
            r"(?i)(?:общая\s+сумма\s+договора|сумма\s+договора)\s*[:=—-]?\s*(\d[\d\s\.,]*\d?)",
            r"(?i)(\d[\d\s]*[\.,]?\d*)\s*(?:uzs|usd|eur|rub)",
            r"(?i)(?:shartnoma\s+summasi|shartnoma\s+narxi|shartnoma\s+bo'yicha\s+ishlar\s+qiymati|jami)\s*[:=]?\s*(\d[\d\s]*[\.,]?\d*)",
        ],
    }
    PARTY_PATTERNS = {
        'party_a_name': [            # First line intro: "DORKOMPLEKTSNAB PLUS" МЧЖ номидан директор ... (кейинги ўринларда «Буюртмачи» деб юритилади)
            # Explicit Uzbek label formats: 1-tomon (Buyurtmachi)
            r"(?im)^\s*(?:1|I)[-\s]*tomon\s*\((?:buyurtmachi|Буюртмачи|zakazchik|Заказчик)\)\s*[:–—-]?\s*([^\n]+)",
            # Same label but name on next line
            r"(?im)^\s*(?:1|I)[-\s]*tomon.*?(?:buyurtmachi|Буюртмачи|zakazchik|Заказчик).*?\n\s*([^\n]{3,200})",
            r'“([A-Z][A-Z\s]+?)”\s+МЧЖ\s+номидан.*?буюртмачи',
            # Avoid matching product table headers like "Наименование товара/услуги"
            r"(?ims)(?:Заказчик|Покупатель).*?Наименование[:\s]+(?!\s*(?:товаров?|услуг[аи]?))([^\n]+?)(?=\s*(?:Телефон|Факс|ИНН|ОКЭД|Адрес|$))",
            # Intro clause definitions: "Буюртмачи" деб юритиладиган "<name>"
            r"(?is)(?:кейинги|keyingi)\s+(?:уринларда|ўринларда|o['’`]?rinlarda)\s*[\"“”']?\s*буюртмачи\s*[\"“”']?\s+деб\s+юритилад(?:и|иг)ган\s*[\"“”']?([^\"”]{3,200})",
            # Line-anchored labels to avoid mid-sentence matches
            r"(?im)(?:^|\n)\s*(?:Заказчик|Покупатель)\s*[:–—-]+\s*([^\n]+)",
            r"(?im)(?:^|\n)\s*(?:Buyurtmachi|Буюртмачи)\s*[:–—-]+\s*([^\n]+)",
            r"(?im)(?:^|\n)\s*(?:1[-\s]*tomon|birinchi\s+tomon|buyurtmachi|zakazchik|заказчик|Буюртмачи)\s*[:–—-]+\s*([^\n]+)",
        ],
        'party_b_name': [            # First line intro: ва "EURO GLOBAL ASPHALT" МЧЖ номидан директор ... (кейинги ўринларда «Етказиб берувчи» деб юритилади)
            # Explicit Uzbek label formats: 2-tomon (Ijrochi/Pudratchi)
            r"(?im)^\s*(?:2|II)[-\s]*tomon\s*\((?:ijrochi|Ижрочи|pudratchi|Пудратчи|podryadchik|Подрядчик|ispolnitel|Исполнитель)\)\s*[:–—-]?\s*([^\n]+)",
            # Same label but name on next line
            r"(?im)^\s*(?:2|II)[-\s]*tomon.*?(?:ijrochi|Ижрочи|pudratchi|Пудратчи|podryadchik|Подрядчик|ispolnitel|Исполнитель).*?\n\s*([^\n]{3,200})",
            r'ва\s+“([A-Z][A-Z\s]+?)”\s+МЧЖ\s+номидан.*?(?:етказиб\s+берувчи|ижрочи)',
            # Avoid matching product table headers like "Наименование товара/услуги"
            r"(?ims)(?:Исполнитель|Поставщик).*?Наименование[:\s]+(?!\s*(?:товаров?|услуг[аи]?))([^\n]+?)(?=\s*(?:Телефон|Факс|ИНН|ОКЭД|Адрес|$))",
            # Intro clause definitions: "Пудратчи/Ижрочи" деб юритиладиган "<name>"
            r"(?is)(?:кейинги|keyingi)\s+(?:уринларда|ўринларда|o['’`]?rinlarda)\s*[\"“”']?\s*(?:пудратчи|ижрочи|pudratchi|ijrochi)\s*[\"“”']?\s+деб\s+юритилад(?:и|иг)ган\s*[\"“”']?([^\"”]{3,200})",
            # Line-anchored labels to avoid mid-sentence matches
            r"(?im)(?:^|\n)\s*(?:Исполнитель|Поставщик|Подрядчик)\s*[:–—-]+\s*([^\n]+)",
            r"(?im)(?:^|\n)\s*(?:Ijrochi|Ижрочи|Pudratchi|Пудратчи|Etkazib\s+beruvchi|Етказиб\s+берувчи)\s*[:–—-]+\s*([^\n]+)",
            r"(?im)(?:^|\n)\s*(?:2[-\s]*tomon|ikkinchi\s+tomon|ijrochi|pudratchi|podryadchik|исполнитель|Пудратчи)\s*[:–—-]+\s*([^\n]+)",
        ],
    }
    
    def __init__(self):
        """Initialize the parser."""
        self.compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        for section_type, patterns in self.SECTION_PATTERNS.items():
            self.compiled_patterns[section_type] = [
                re.compile(p, re.MULTILINE | re.UNICODE)
                for p in patterns
            ]
    
    def parse(self, text: str) -> Tuple[List[Section], ContractMetadata]:
        """
        Parse contract text and extract sections and metadata.
        
        Args:
            text: Contract text
            
        Returns:
            Tuple of (sections list, metadata)
        """
        # Normalize text to improve section/metadata detection
        text = self._normalize_text(text)
        # Extract metadata
        metadata = self._extract_metadata(text)
        
        # Find section boundaries
        section_positions = self._find_section_positions(text)
        
        # Extract sections
        sections = self._extract_sections(text, section_positions)
        
        # Extract clauses within each section
        for section in sections:
            section.clauses = self._extract_clauses(section.content, section.section_type)
        
        return sections, metadata

    def _normalize_text(self, text: str) -> str:
        """Normalize common OCR artifacts (hyphenation, apostrophes, spaces, EOLs)."""
        if not text:
            return text
        # Harmonize mixed Latin/Cyrillic lookalike letters in Cyrillic-dominant texts
        try:
            total_letters = sum(1 for c in text if c.isalpha())
            cyr_letters = sum(1 for c in text if 'А' <= c <= 'я' or c in 'ЁёЎўҒғҚқҲҳ')
            cyr_ratio = (cyr_letters / total_letters) if total_letters else 0
            if cyr_ratio >= 0.6:
                # Map Latin lookalikes to Cyrillic to fix headers like "ШАРТНОМA" → "ШАРТНОМА"
                latin_to_cyr = {
                    'A': 'А', 'a': 'а',
                    'B': 'В', 'b': 'в',
                    'E': 'Е', 'e': 'е',
                    'K': 'К', 'k': 'к',
                    'M': 'М', 'm': 'м',
                    'H': 'Н', 'h': 'н',
                    'O': 'О', 'o': 'о',
                    'P': 'Р', 'p': 'р',
                    'C': 'С', 'c': 'с',
                    'T': 'Т', 't': 'т',
                    'X': 'Х', 'x': 'х',
                    'Y': 'У', 'y': 'у',  # careful but helps for full-uppercase headings
                }
                text = ''.join(latin_to_cyr.get(ch, ch) for ch in text)
        except Exception:
            # If anything goes wrong, keep original text
            pass
        # Join hyphenation broken at EOL: word-\nword -> wordword
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
        # Normalize apostrophes/backticks/quotes to a single apostrophe
        text = text.replace("`", "'")
        text = text.replace("’", "'").replace("ʻ", "'").replace("ʼ", "'").replace("‘", "'")
        # Collapse multiple spaces
        text = re.sub(r"[ \t]{2,}", " ", text)
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Insert newlines before numbered headings that often get concatenated in OCR
        # e.g., "... Сторона, заключили ... 1. ПРЕДМЕТ ДОГОВОРА" -> place newline before "1."
        # Also support Roman numerals and Cyrillic letters as section prefixes (П., Ш., I., II., etc.)
        text = re.sub(r"(?<!\n)(\s)((?:[\dIVX]+|[A-ZА-ЯЁЎҚҲҒ]{1,3})[\.\)]\s*[A-ZА-ЯЁЎҚҲҒ])", r"\1\n\2", text)
        # Insert newlines before common Russian/Uzbek section headers if missing line breaks
        header_keywords = [
            r"ПРЕДМЕТ ДОГОВОРА", r"ЦЕНА ДОГОВОРА", r"ПОРЯДОК РАСЧЕТОВ", r"СРОК ДЕЙСТВИЯ",
            r"ОТВЕТСТВЕННОСТЬ", r"ЮРИДИЧЕСКИЕ АДРЕСА", r"РЕКВИЗИТЫ СТОРОН",
            r"ШАРТНОМА МАВЗУСИ", r"ШАРТНОМА БЎЙИЧА ИШЛАР ҚИЙМАТИ", r"ИШЛАРНИ БAЖАРИШ МУДДАТЛАРИ",
            r"Шартнома предмети", r"Narx", r"Muddat", r"Javobgarlik", r"Rekvizitlari",
            r"ШАРТНОМАНИНГ БАҲОСИ", r"ҲИСОБ-КИТОБ", r"БАНК РЕКВИЗИТЛАРИ", r"ШАРТНОМАНИНГ АМАЛ ҚИЛИШИ"
        ]
        for kw in header_keywords:
            text = re.sub(rf"(?<!\n)\s({kw})", r"\n\1", text, flags=re.IGNORECASE)
        return text
    
    def _extract_metadata(self, text: str) -> ContractMetadata:
        """Extract metadata from contract text."""
        metadata = ContractMetadata()
        
        # Extract contract number
        for pattern in self.METADATA_PATTERNS['contract_number']:
            match = re.search(pattern, text)
            if match:
                metadata.contract_number = match.group(1)
                break
        
        # Extract contract date
        for pattern in self.METADATA_PATTERNS['contract_date']:
            match = re.search(pattern, text)
            if match:
                metadata.contract_date = match.group(0)
                break
        
        # Extract INNs - try multiple patterns
        import logging
        logger_local = logging.getLogger(__name__)
        
        # First, try to extract from requisites section only (most reliable)
        requisites_anchors = [
            r"ЮРИДИЧЕСКИЕ\s+АДРЕСА",
            r"РЕКВИЗИТЫ\s+СТОРОН",
            r"ТОМОНЛАРНИНГ\s+РЕКВИЗИТЛАРИ",
            r"TOMONLARNING\s+REKVIZITLARI",
            r"ЮРИДИК\s+МАНЗИЛЛАР",
            r"REKVIZIT",
        ]
        requisites_text = ""
        for anchor in requisites_anchors:
            for m in re.finditer(anchor, text, flags=re.IGNORECASE):
                # Get 2000 chars after anchor
                requisites_text = text[m.start():m.start()+2000]
                break
            if requisites_text:
                break
        
        # Extract INNs from requisites first
        all_inns = []
        if requisites_text:
            # Try INN label pattern first in requisites
            inn_from_label = re.findall(r"(?i)(?:INN|ИНН)\s*(\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d)", requisites_text)
            if inn_from_label:
                all_inns.extend(inn_from_label)
                logger_local.info(f"[INN_EXTRACT] From requisites INN labels: {inn_from_label}")
        
        # If not enough from requisites, try full text
        if len(all_inns) < 2:
            for pattern in self.METADATA_PATTERNS['inn']:
                inns = re.findall(pattern, text)
                logger_local.info(f"[INN_EXTRACT] Pattern '{pattern[:50]}...': found {len(inns)} matches")
                if inns:
                    all_inns.extend(inns)
        
        # Normalize INNs (remove spaces/dashes from within)
        normalized_inns = []
        for inn in all_inns:
            normalized_inn = re.sub(r'[\s–-]', '', inn)  # Remove spaces and dashes
            if len(normalized_inn) == 9 and normalized_inn.isdigit():  # Valid 9-digit INN
                normalized_inns.append(normalized_inn)
                logger_local.info(f"[INN_EXTRACT] Valid INN: {inn} -> {normalized_inn}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_inns = []
        for inn in normalized_inns:
            if inn not in seen:
                seen.add(inn)
                unique_inns.append(inn)
        
        # Take only the first two (if more, discard extras likely from OCR corruption)
        unique_inns = unique_inns[:2]
        
        logger_local.info(f"[INN_EXTRACT] Final unique INNs: {unique_inns}")
        if len(unique_inns) >= 1:
            metadata.party_a_inn = unique_inns[0]
        if len(unique_inns) >= 2:
            metadata.party_b_inn = unique_inns[1]
        
        # Heuristic: derive party names near INN lines in requisites/signature blocks when explicit labels are missing
        try:
            def _extract_blocks(req_text: str) -> List[Dict[str, Optional[str]]]:
                blocks: List[Dict[str, Optional[str]]] = []
                if not req_text:
                    return blocks
                # Define label patterns for two blocks
                label_a = re.compile(r"(?ims)[“\«]\s*(?:Заказчик|Покупатель|Буюртмачи|Buyurtmachi|Пудратчи|ПУДРАТЧИ)\s*[”\»]")
                label_b = re.compile(r"(?ims)[“\«]\s*(?:Исполнитель|Поставщик|Подрядчик|Ижрочи|Ijrochi|Етказиб\s+берувчи|Etkazib\s+beruvchi|Ёрдамчи\s+Пудратчи|ЁРДАМЧИ\s+ПУДРАТЧИ)\s*[”\»]")
                # Find all label occurrences with type
                labels = []
                for m in label_a.finditer(req_text):
                    labels.append(('A', m.start()))
                for m in label_b.finditer(req_text):
                    labels.append(('B', m.start()))
                if not labels:
                    return blocks
                labels.sort(key=lambda x: x[1])
                # Find ordered org names with markers across requisites
                names = [nm.group(1).strip() for nm in re.finditer(r"[“\«]([^”\»\n]{3,200})[”\»]\s+(?:МЧЖ|АЖ|ООО|АО|AJ)", req_text)]
                # Pair names to labels by order
                count = min(len(labels), len(names))
                for i in range(count):
                    typ, pos = labels[i]
                    name_val = names[i]
                    # Extract nearest INN after label position within 800 chars
                    seg = req_text[pos:pos+800]
                    im = re.search(r"(?i)(?:ИНН|INN|STIR)[\s:–-]*(\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d)", seg)
                    inn_val = None
                    if im:
                        inn_raw = im.group(1)
                        inn_norm = re.sub(r"[\s–-]", "", inn_raw)
                        if len(inn_norm) == 9 and inn_norm.isdigit():
                            inn_val = inn_norm
                    blocks.append({'type': typ, 'name': name_val, 'inn': inn_val})
                return blocks
            def _pair_names_with_inns(req_text: str) -> List[Tuple[str, str]]:
                pairs: List[Tuple[str, str]] = []
                if not req_text:
                    return pairs
                org_markers = r"(?:МЧЖ|АЖ|ООО|АО|ЗАО|ОАО|AJ)"
                # Find quoted org names and try to associate with the nearest subsequent INN
                for nm in re.finditer(rf"[“\«]([^”\»\n]{{3,200}})[”\»]\s+{org_markers}", req_text):
                    name = nm.group(1).strip()
                    # Look ahead 500 chars for an INN label and digits
                    look_start = nm.end()
                    look_end = min(len(req_text), look_start + 500)
                    look = req_text[look_start:look_end]
                    inn_m = re.search(r"(?i)(?:ИНН|INN|STIR)[\s:–-]*(\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d[\s–-]*\d)", look)
                    if inn_m:
                        inn_raw = inn_m.group(1)
                        inn_norm = re.sub(r"[\s–-]", "", inn_raw)
                        if len(inn_norm) == 9 and inn_norm.isdigit():
                            pairs.append((name, inn_norm))
                return pairs

            def _find_name_near_inn(full_text: str, inn_numeric: str, label_regex: Optional[str] = None) -> Optional[str]:
                # Build a permissive pattern that matches the INN digits with optional spaces/dashes
                inn_pat = ''.join([f"{d}[\\s–-]*" for d in inn_numeric])
                m = re.search(inn_pat, full_text)
                if not m:
                    return None
                # Take a window before the INN occurrence to search for organization names
                start = max(0, m.start() - 3000)
                end = min(len(full_text), m.end() + 2000)
                window = full_text[start:end]
                # Common org type markers (Uz/Ru)
                org_markers = r"(?:МЧЖ|АЖ|ООО|АО|ЗАО|ОАО|ИП|ЧП|СП|AJ|МЖ)"
                candidates_before: List[Tuple[int, str]] = []  # (distance, name)
                candidates_after: List[Tuple[int, str]] = []   # (distance, name)
                label_candidates_before: List[Tuple[int, str]] = []
                label_candidates_after: List[Tuple[int, str]] = []
                # Label-anchored capture: e.g., Заказчик/Исполнитель/Пудратчи → Наименование: <name>
                if label_regex:
                    for lm in re.finditer(rf"(?ims)(?:^|\n)\s*(?:{label_regex}).{{0,250}}?Наименование[:\s]+(?!\s*(?:товаров?|услуг[аи]?))([^\n]+)", window):
                        name = lm.group(1).strip().strip('“”«»')
                        pos = start + lm.start()
                        dist = abs(m.start() - pos)
                        if pos <= m.start():
                            label_candidates_before.append((dist, name))
                        else:
                            label_candidates_after.append((dist, name))
                    # Also capture quoted names with org markers under label blocks
                    for qm in re.finditer(rf"(?ims)(?:^|\n)\s*(?:{label_regex}).{{0,500}}?[“\«]([^”\»\n]{{3,200}})[”\»]\s+(?:МЧЖ|АЖ|ООО|АО|AJ)", window):
                        name = qm.group(1).strip()
                        pos = start + qm.start()
                        dist = abs(m.start() - pos)
                        if pos <= m.start():
                            label_candidates_before.append((dist, name))
                        else:
                            label_candidates_after.append((dist, name))
                # Generic capture: any 'Наименование: <name>' in proximity
                for nm in re.finditer(r"(?im)(?:^|\n)\s*Наименование[:\s]+(?!\s*(?:товаров?|услуг[аи]?))([^\n]+)", window):
                    name = nm.group(1).strip().strip('“”«»')
                    pos = start + nm.start()
                    dist = abs(m.start() - pos)
                    if pos <= m.start():
                        candidates_before.append((dist, name))
                    else:
                        candidates_after.append((dist, name))
                # Prefer quoted names followed by org marker: “NAME” МЧЖ / «NAME» АЖ
                for qm in re.finditer(rf"[“\«]([^”\»\n]{{3,200}})[”\»]\s+{org_markers}", window, re.IGNORECASE):
                    name = qm.group(1).strip()
                    # Position of match relative to full_text
                    pos = start + qm.start()
                    dist = abs(m.start() - pos)
                    if pos <= m.start():
                        candidates_before.append((dist, name))
                    else:
                        candidates_after.append((dist, name))
                # Fallback: unquoted line with org marker
                for um in re.finditer(rf"(?im)^\s*([A-Za-z0-9А-ЯЁЎҚҲҒҒҲЇІЄӢӮЁёЎўҒғҚқҲҳ\-\.'\s]{{3,200}})\s+{org_markers}.*$", window):
                    name = um.group(1).strip()
                    pos = start + um.start()
                    dist = abs(m.start() - pos)
                    if pos <= m.start():
                        candidates_before.append((dist, name))
                    else:
                        candidates_after.append((dist, name))
                # Prefer label-derived candidates first
                if label_candidates_before or label_candidates_after:
                    label_candidates_before.sort(key=lambda x: x[0])
                    label_candidates_after.sort(key=lambda x: x[0])
                    best_before = label_candidates_before[0] if label_candidates_before else (10**9, '')
                    best_after = label_candidates_after[0] if label_candidates_after else (10**9, '')
                else:
                    # Fall back to generic candidates
                    candidates_before.sort(key=lambda x: x[0])
                    candidates_after.sort(key=lambda x: x[0])
                    best_before = candidates_before[0] if candidates_before else (10**9, '')
                    best_after = candidates_after[0] if candidates_after else (10**9, '')
                    # If preceding is very far and a following candidate is closer, use following
                    if best_before[0] > 500 and best_after[0] < best_before[0]:
                        return best_after[1]
                    if best_before[1]:
                        return best_before[1]
                    if best_after[1]:
                        return best_after[1]
                # Another fallback: header-like single line before INN
                lines = window.split("\n")
                for idx in range(len(lines)-1, -1, -1):
                    ln = lines[idx]
                    ln_stripped = ln.strip()
                    if len(ln_stripped) >= 3 and any(k in ln_stripped for k in ["МЧЖ", "АЖ", "ООО", "АО"]):
                        # Attempt to take name portion before marker
                        name = re.split(r"\s+(?:МЧЖ|АЖ|ООО|АО)\b", ln_stripped)[0].strip('“”«» \t')
                        if name:
                            return name
                return None

            # Choose a robust search area: requisites_text if present, else tail of the document
            search_area = requisites_text or text[-8000:]
            # Try block-based extraction for ordered mapping
            try:
                blocks = _extract_blocks(search_area)
                if blocks:
                    # Assign names by matching INNs where possible, else by order
                    for b in blocks:
                        if b.get('inn') and b.get('name'):
                            if metadata.party_a_inn == b['inn'] and not metadata.party_a_name:
                                metadata.party_a_name = b['name']
                            if metadata.party_b_inn == b['inn'] and not metadata.party_b_name:
                                metadata.party_b_name = b['name']
                    # Fallback by order if still missing
                    names_ordered = [b['name'] for b in blocks if b.get('name')]
                    if names_ordered:
                        if not metadata.party_a_name and len(names_ordered) >= 1:
                            metadata.party_a_name = names_ordered[0]
                        if not metadata.party_b_name and len(names_ordered) >= 2:
                            metadata.party_b_name = names_ordered[1]
                    # If both names ended up identical but blocks yielded two distinct names, override by order
                    if (metadata.party_a_name and metadata.party_b_name and metadata.party_a_name == metadata.party_b_name) and len(names_ordered) >= 2:
                        a_name_new, b_name_new = names_ordered[0], names_ordered[1]
                        if a_name_new and b_name_new and a_name_new != b_name_new:
                            logger_local.info(f"[PARTY_BLOCK_OVERRIDE] Overriding identical names → A='{a_name_new}', B='{b_name_new}'")
                            metadata.party_a_name = a_name_new
                            metadata.party_b_name = b_name_new
            except Exception:
                pass
            # First, try pairing names with INNs directly from requisites
            try:
                pairs = _pair_names_with_inns(search_area)
                if pairs:
                    for n, i in pairs:
                        if metadata.party_a_inn == i:
                            metadata.party_a_name = metadata.party_a_name or n
                        if metadata.party_b_inn == i:
                            metadata.party_b_name = metadata.party_b_name or n
            except Exception:
                pass
            if metadata.party_a_inn and not metadata.party_a_name:
                name_a = _find_name_near_inn(search_area, metadata.party_a_inn, label_regex=r"Заказчик|Покупатель|Буюртмачи|Buyurtmachi|Пудратчи|ПУДРАТЧИ")
                if name_a:
                    logger_local.info(f"[PARTY_NEAR_INN] party_a_name inferred: {name_a[:120]}")
                    metadata.party_a_name = name_a
            if metadata.party_b_inn and not metadata.party_b_name:
                name_b = _find_name_near_inn(search_area, metadata.party_b_inn, label_regex=r"Исполнитель|Поставщик|Подрядчик|Ижрочи|Ijrochi|Етказиб\s+берувчи|Etkazib\s+beruvchi|Ёрдамчи\s+Пудратчи|ЁРДАМЧИ\s+ПУДРАТЧИ")
                if name_b:
                    logger_local.info(f"[PARTY_NEAR_INN] party_b_name inferred: {name_b[:120]}")
                    metadata.party_b_name = name_b
            # If still missing, try capturing organization names by markers in requisites area
            if (not metadata.party_a_name or not metadata.party_b_name):
                org_pairs = re.findall(r"[“\«]([^”\»\n]{3,200})[”\»]\s+(МЧЖ|АЖ|ООО|АО)", search_area, re.IGNORECASE)
                if org_pairs:
                    org_names = [n.strip() for n, _ in org_pairs]
                    # Deduplicate while preserving order
                    seen_n = set(); ordered = []
                    for n in org_names:
                        if n and n not in seen_n:
                            seen_n.add(n); ordered.append(n)
                    if not metadata.party_a_name and len(ordered) >= 1:
                        metadata.party_a_name = ordered[0]
                        logger_local.info(f"[PARTY_MARKERS] party_a_name from markers: {ordered[0][:120]}")
                    if not metadata.party_b_name and len(ordered) >= 2:
                        metadata.party_b_name = ordered[1]
                        logger_local.info(f"[PARTY_MARKERS] party_b_name from markers: {ordered[1][:120]}")

            # If both names ended up identical but the string contains two organization names,
            # attempt to split into distinct A/B names
            try:
                if metadata.party_a_name and metadata.party_b_name and metadata.party_a_name == metadata.party_b_name:
                    dual = re.findall(r"[“\«]([^”\»\n]{3,200})[”\»]\s+(МЧЖ|АЖ|ООО|АО|AJ)", metadata.party_a_name)
                    if len(dual) >= 2:
                        a_name = dual[0][0].strip(); b_name = dual[1][0].strip()
                        logger_local.info(f"[PARTY_SPLIT] Detected two org names in combined string → A='{a_name}', B='{b_name}'")
                        metadata.party_a_name, metadata.party_b_name = a_name, b_name
            except Exception:
                pass
        except Exception as e:
            logger_local.info(f"[PARTY_NEAR_INN] Heuristic failed: {e}")
        
        # Extract amount
        for pattern in self.METADATA_PATTERNS['amount']:
            match = re.search(pattern, text)
            if match:
                amount_raw = match.group(1).strip()
                logger_local.info(f"[AMOUNT_EXTRACT] Pattern matched: '{pattern[:80]}...', raw: '{amount_raw[:80]}'")
                # Skip very small numbers (< 100,000) using robust numeric parsing
                amount_clean = re.sub(r'[\s–-]', '', amount_raw)
                skip_small = False
                try:
                    amount_val_float = float(amount_clean.replace(',', '.'))
                    if amount_val_float < 50000:
                        skip_small = True
                except Exception:
                    # Fallback: digits-only compare
                    digits_only = re.sub(r'[^0-9]', '', amount_raw)
                    if digits_only and digits_only.isdigit():
                        try:
                            if int(digits_only) < 50000:
                                skip_small = True
                        except Exception:
                            pass
                if skip_small:
                    logger_local.info(f"[AMOUNT_EXTRACT] Skipping small number: {amount_clean}")
                    continue

                # Store a normalized numeric string representing whole currency units
                normalized_numeric: str
                try:
                    # Prefer robust float parsing, then round to whole units
                    parsed = float(amount_clean.replace(',', '.'))
                    normalized_numeric = str(int(round(parsed)))
                except Exception:
                    # Fallback: digits-only, but avoid inflating values with decimals
                    # If raw contains a decimal part, drop it instead of concatenating
                    if '.' in amount_clean or ',' in amount_clean:
                        digits_before = re.sub(r'[^0-9].*$', '', amount_clean)
                        normalized_numeric = re.sub(r'[^0-9]', '', digits_before)
                    else:
                        normalized_numeric = re.sub(r'[^0-9]', '', amount_raw)

                logger_local.info(f"[AMOUNT_EXTRACT] Found: '{amount_raw[:50]}...' -> '{normalized_numeric}'")
                # Faqat eng katta sonni saqlash
                if not metadata.total_amount or int(normalized_numeric) > int(metadata.total_amount):
                    metadata.total_amount = normalized_numeric
                    logger_local.info(f"[AMOUNT_EXTRACT] Updated to larger amount: {normalized_numeric}")
                # Break emas, barcha patternlarni tekshiramiz
        
        # Fallback: If amount not found in header, search for formatted currency amounts (e.g., "5 600 000 000")
        if not metadata.total_amount:
            logger_local.info("[AMOUNT_EXTRACT] Amount not found in main patterns, searching for formatted amounts...")
            # Look for formatted amounts with NBSP as thousands separators
            # May be followed by parenthetical text (e.g., Russian/Uzbek word representation)
            formatted_amount_patterns = [
                # Pattern: number with NBSP, optional decimal, optional parenthetical, then currency
                r"(5\xa0600\xa0000\xa0000\.00)\s*\([^)]*\)\s*сўмни",  # Specific pattern for 5.6B
                r"(\d[\d\xa0]+\.?\d*)\s*(?:\([^)]*\))?\s*(?:сўмни|сум)",  # General flexible pattern
                r"(\d{1,3}(?:\xa0\d{3})+(?:\.\d{1,3})?)\s*(?:сўмни|сумни|сум|сўм)",  # NBSP-specific
            ]
            for pattern in formatted_amount_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for amount_raw in matches:
                        logger_local.info(f"[AMOUNT_EXTRACT] Fallback found: '{amount_raw}'")
                        # Normalize spaces (both regular and NBSP) for parsing
                        amount_clean = re.sub(r'[\s\xa0\-–—]', '', amount_raw)
                        try:
                            parsed = float(amount_clean.replace(',', '.'))
                            normalized_numeric = str(int(round(parsed)))
                            if int(normalized_numeric) >= 100000:
                                if not metadata.total_amount or int(normalized_numeric) > int(metadata.total_amount):
                                    metadata.total_amount = normalized_numeric
                                    logger_local.info(f"[AMOUNT_EXTRACT] Updated fallback to larger amount: '{normalized_numeric}'")
                        except Exception as e:
                            logger_local.info(f"[AMOUNT_EXTRACT] Failed to parse: {e}")
                    if metadata.total_amount:
                        break
        
        # Fallback: if no amount found, search more aggressively in requisites
        if not metadata.total_amount:
            # Try specific section header: "ШАРТНОМА БУЙИЧА ИШЛАР КИЙМАТИ" or "Ш. ШАРТНОМА"
            section_match = re.search(r"(?i)(?:ш\.|шартнома буйича ишлар киймати).*?(?:сумни|сумлик)\s+(\d[\d\s]+?)\s*(?:\(|сум)", text, re.DOTALL)
            if section_match:
                amount_val = re.sub(r'[\s–-]', '', section_match.group(1).strip())
                if len(amount_val) >= 10:  # Reasonable contract amount
                    logger_local.info(f"[AMOUNT_EXTRACT] Section found: '{section_match.group(1).strip()}' -> '{amount_val}'")
                    metadata.total_amount = amount_val
        
        # If still no valid amount or too small, try one more search
        try:
            if not metadata.total_amount or (metadata.total_amount and float(metadata.total_amount) < 100000):
                # Search for 270 460 577 128 pattern anywhere
                large_amount = re.search(r'(\d{3,4}[\s]+\d{3}[\s]+\d{3}[\s]+\d{3})', text)
                if large_amount:
                    amount_val = re.sub(r'[\s–-]', '', large_amount.group(1))
                    logger_local.info(f"[AMOUNT_EXTRACT] Large amount pattern found: {amount_val}")
                    metadata.total_amount = amount_val
        except (ValueError, TypeError):
            pass
        
        # Detect currency
        if 'USD' in text.upper() or '$' in text:
            metadata.currency = 'USD'
        elif 'EUR' in text.upper() or '€' in text:
            metadata.currency = 'EUR'
        else:
            metadata.currency = 'UZS'
        
        # Detect language
        metadata.language = self._detect_language(text)
        
        if not metadata.party_a_name:
            metadata.party_a_name = self._extract_party(text, 'party_a_name')
        if not metadata.party_b_name:
            metadata.party_b_name = self._extract_party(text, 'party_b_name')

        # Final fallback: if names still missing or identical, try INN registry mapping
        try:
            identical = (metadata.party_a_name and metadata.party_b_name and metadata.party_a_name == metadata.party_b_name)
            if (not metadata.party_a_name) or identical:
                if metadata.party_a_inn:
                    resolved = resolve_inn_name(metadata.party_a_inn)
                    if resolved:
                        metadata.party_a_name = resolved
            if (not metadata.party_b_name) or identical:
                if metadata.party_b_inn:
                    resolved = resolve_inn_name(metadata.party_b_inn)
                    if resolved:
                        metadata.party_b_name = resolved
        except Exception:
            pass

        return metadata

    def _extract_party(self, text: str, field: str) -> Optional[str]:
        """Extract party name using defined patterns."""
        import logging
        logger = logging.getLogger(__name__)
        
        # First, try to find the requisites section (typically at end with "9. Юридические адреса")
        requisites_anchors = [
            r"ЮРИДИЧЕСКИЕ\s+АДРЕСА",
            r"РЕКВИЗИТЫ\s+СТОРОН",
            r"ТОМОНЛАРНИНГ\s+РЕКВИЗИТЛАРИ",
            r"TOMONLARNING\s+REKVIZITLARI",
            r"ЮРИДИК\s+МАНЗИЛЛАР",
            r"REKVIZIT",
        ]
        anchor_match = None
        for anchor in requisites_anchors:
            for m in re.finditer(anchor, text, flags=re.IGNORECASE):
                anchor_match = m

        search_blocks = []
        # First search in intro (first 3000 chars) for party names in contract opening
        search_blocks.append(text[:3000])
        logger.info(f"[PARTY_EXTRACT] Added intro block (first 3000 chars) to search")
        if anchor_match:
            search_blocks.append(text[anchor_match.start():])
            logger.info(f"[PARTY_EXTRACT] Found requisites anchor '{anchor_match.group(0)}', searching within it")
        else:
            logger.info(f"[PARTY_EXTRACT] No requisites section found, searching last 50k chars")

        search_blocks.append(text[-50000:])
        logger.info(f"[PARTY_EXTRACT] Total search blocks: {len(search_blocks)}")

        for block_idx, search_text in enumerate(search_blocks):
            print(f"[DEBUG PARTY] Block {block_idx+1}/{len(search_blocks)}, length={len(search_text)}, field={field}")
            logger.info(f"[PARTY_EXTRACT] Searching block {block_idx+1}/{len(search_blocks)} (length: {len(search_text)})")
            for pattern_idx, pattern in enumerate(self.PARTY_PATTERNS.get(field, [])):
                print(f"[DEBUG PARTY] Testing pattern {pattern_idx+1}: {repr(pattern[:60])}")
                match = re.search(pattern, search_text)
                if match:
                    print(f"[DEBUG PARTY] MATCH FOUND: {match.group(1)[:50]}")
                    value = match.group(1).strip()
                    logger.info(f"[PARTY_EXTRACT] {field} matched pattern {pattern_idx+1}, raw value: {value[:100]}")
                    
                    # Stop at common delimiters that usually introduce requisites or amounts
                    value = re.split(r"\b(?:ИНН|INN|STIR|Адрес|Address|Телефон|Факс|ОКЭД|Банк|Р/С|р/с|МФО)\b", value)[0].strip()
                    logger.info(f"[PARTY_EXTRACT] {field} after split: {value[:100]}")

                    # Filter out obvious table header noise often mis-captured as party name
                    noise_keywords = [
                        "Штрих-код", "Единицы", "Стоимость", "электронному", "Кол-во", "Цена",
                        "ставка", "учётом НДС", "с учётом НДС", "товаров", "товара", "услуг", "услуги",
                        "национальному каталогу", "каталогу", "Laboratoriya"
                    ]
                    if any(k.lower() in value.lower() for k in noise_keywords):
                        logger.info(f"[PARTY_EXTRACT] {field} rejected as noise: {value[:100]}")
                        continue
                    
                    # Keep a reasonable length to avoid swallowing large tables
                    if len(value) > 200:
                        value = value[:200].rstrip()
                        logger.info(f"[PARTY_EXTRACT] {field} truncated to 200 chars")
                        
                    return value
        logger.info(f"[PARTY_EXTRACT] {field} - NO MATCH")
        return None
    
    def _detect_language(self, text: str) -> str:
        """Detect contract language: Russian, Uzbek Cyrillic, or Latin."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Priority check: look for "Договор" in first 2000 chars (strong Russian marker)
        if re.search(r'(?i)\bДоговор\b', text[:2000]):
            logger.info("[LANG_DETECT] RETURNING: ru (found 'Договор' keyword)")
            return 'ru'
        
        cyrillic = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        russian_specific = set('ъыэё')
        uzbek_specific = set("ғҳқўшчђҷ")
        
        cyrillic_count = sum(1 for c in text if c in cyrillic)
        russian_count = sum(1 for c in text if c in russian_specific)
        uzbek_indicator = sum(1 for c in text if c in uzbek_specific)
        total_letters = sum(1 for c in text if c.isalpha())
        
        if total_letters == 0:
            return 'uz-latn'
        
        cyrillic_ratio = cyrillic_count / total_letters
        
        logger.info(f"[LANG_DETECT] cyrillic_count={cyrillic_count}, russian_count={russian_count}, uzbek_indicator={uzbek_indicator}, total_letters={total_letters}, cyrillic_ratio={cyrillic_ratio:.2%}")
        
        if cyrillic_ratio > 0.5:
            # If Uzbek-specific letters dominate, prefer Uzbek Cyrillic even when Russian letters exist
            if uzbek_indicator >= 5 and uzbek_indicator >= max(1, russian_count // 2):
                logger.info(f"[LANG_DETECT] RETURNING: uz-cyrl (uzbek chars dominate: uzbek_indicator={uzbek_indicator}, russian_count={russian_count})")
                return 'uz-cyrl'

            # Check for Russian-specific words
            russian_words = ['договор', 'поставщик', 'исполнитель', 'заказчик', 'покупатель', 'условиях', 'расчетов']
            russian_word_count = sum(1 for word in russian_words if word in text.lower())
            
            logger.info(f"[LANG_DETECT] russian_word_count={russian_word_count}, words found: {[w for w in russian_words if w in text.lower()]}")
            
            # If Russian-specific characters detected, it's Russian
            if russian_count >= 5:
                logger.info(f"[LANG_DETECT] RETURNING: ru (has russian_specific chars: russian_count={russian_count})")
                return 'ru'
            
            # If Russian-specific words detected (high confidence), it's Russian
            if russian_word_count >= 5:
                logger.info(f"[LANG_DETECT] RETURNING: ru (has many russian_words: russian_word_count={russian_word_count})")
                return 'ru'
            
            # If some Russian words and no Uzbek characters, it's Russian
            if russian_word_count >= 2 and uzbek_indicator == 0:
                logger.info(f"[LANG_DETECT] RETURNING: ru (russian_words + no uzbek chars)")
                return 'ru'
            
            # If Uzbek-specific letters present, prefer Uzbek Cyrillic (mixed contracts)
            if uzbek_indicator >= 1:
                logger.info(f"[LANG_DETECT] RETURNING: uz-cyrl (uzbek_indicator={uzbek_indicator})")
                return 'uz-cyrl'
            
            # Default to Uzbek Cyrillic for ambiguous Cyrillic text
            logger.info(f"[LANG_DETECT] RETURNING: uz-cyrl (default for ambiguous)")
            return 'uz-cyrl'
        
        logger.info(f"[LANG_DETECT] RETURNING: uz-latn (cyrillic_ratio too low)")
        return 'uz-latn'
    
    def _find_section_positions(self, text: str) -> List[Tuple[int, int, SectionType, str]]:
        """Find positions of all sections in text."""
        positions = []
        
        for section_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    positions.append((
                        match.start(),
                        match.end(),
                        section_type,
                        match.group(0).strip()
                    ))
        
        if positions:
            # If multiple section types start at the same position, prefer more specific matches.
            priority = {
                SectionType.REQUISITES: 1,
                SectionType.LIABILITY: 2,
                SectionType.TERM: 3,
                SectionType.PRICE: 4,
                SectionType.SUBJECT: 5,
                SectionType.PARTIES: 9,
            }
            filtered = {}
            for start, end, stype, title in positions:
                existing = filtered.get(start)
                if not existing:
                    filtered[start] = (start, end, stype, title)
                else:
                    current_priority = priority.get(stype, 50)
                    existing_priority = priority.get(existing[2], 50)
                    if current_priority < existing_priority:
                        filtered[start] = (start, end, stype, title)
            positions = list(filtered.values())

        # Sort by position
        positions.sort(key=lambda x: x[0])

        # Remove exact duplicates (same start and type) but keep nearby distinct headings
        unique_positions = []
        seen = set()
        for pos in positions:
            key = (pos[0], pos[2])
            if key in seen:
                continue
            seen.add(key)
            unique_positions.append(pos)
        
        return unique_positions
    
    def _extract_sections(self, text: str, positions: List[Tuple[int, int, SectionType, str]]) -> List[Section]:
        """Extract sections based on found positions."""
        sections = []
        
        # Add header section (text before first section)
        if positions and positions[0][0] > 0:
            header_text = text[:positions[0][0]].strip()
            if header_text:
                sections.append(Section(
                    section_type=SectionType.HEADER,
                    title="Sarlavha",
                    number="",
                    content=header_text,
                    start_pos=0,
                    end_pos=positions[0][0]
                ))
        
        # Extract each section
        for i, (start, header_end, section_type, title) in enumerate(positions):
            # Determine end position
            if i + 1 < len(positions):
                end = positions[i + 1][0]
            else:
                end = len(text)
            
            content = text[header_end:end].strip()
            
            # Extract section number from title
            number_match = re.match(r'^(\d+)[\.\)]', title)
            number = number_match.group(1) if number_match else ""
            
            sections.append(Section(
                section_type=section_type,
                title=title,
                number=number,
                content=content,
                start_pos=start,
                end_pos=end
            ))
        
        return sections
    
    def _extract_clauses(self, content: str, section_type: SectionType) -> List[Clause]:
        """Extract individual clauses from section content."""
        clauses = []
        
        # Pattern for numbered clauses like "1.1", "2.3.1", etc.
        clause_pattern = re.compile(
            r'(?:^|\n)\s*(\d+(?:\.\d+)*)[\.:\)]\s*(.+?)(?=(?:\n\s*\d+(?:\.\d+)*[\.:\)])|$)',
            re.DOTALL
        )
        
        for match in clause_pattern.finditer(content):
            clause_number = match.group(1)
            clause_content = match.group(2).strip()
            
            if clause_content:
                clauses.append(Clause(
                    number=clause_number,
                    content=clause_content,
                    section_type=section_type,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return clauses
    
    def get_section_by_type(self, sections: List[Section], section_type: SectionType) -> Optional[Section]:
        """Get section by type."""
        for section in sections:
            if section.section_type == section_type:
                return section
        return None
    
    def get_missing_sections(self, sections: List[Section], required_types: List[SectionType]) -> List[SectionType]:
        """Find missing required sections."""
        found_types = {s.section_type for s in sections}
        return [t for t in required_types if t not in found_types]
