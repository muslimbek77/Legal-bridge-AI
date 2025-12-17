"""
Contract Parser Module.
Parses contract text and extracts structured sections and clauses.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

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
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:SHARTNOMA\s+PREDMETI|ПРЕДМЕТ\s+ДОГОВОРА|Shartnoma\s+mavzusi)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:PREDMET|MAVZU)",
        ],
        SectionType.PARTIES: [
            r"(?i)(?:^|\n)\s*(?:TOMONLAR|СТОРОНЫ|Taraflar)",
            r"(?i)bir\s+tomondan.*boshqa\s+tomondan",
            r"(?i)с\s+одной\s+стороны.*с\s+другой\s+стороны",
        ],
        SectionType.RIGHTS: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:TOMONLARNING\s+HUQUQLARI|ПРАВА\s+СТОРОН|Huquqlar)",
        ],
        SectionType.OBLIGATIONS: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:TOMONLARNING\s+MAJBURIYATLARI|ОБЯЗАННОСТИ\s+СТОРОН|Majburiyatlar)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:HUQUQ\s+VA\s+MAJBURIYATLAR|ПРАВА\s+И\s+ОБЯЗАННОСТИ)",
        ],
        SectionType.PRICE: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:SHARTNOMA\s+NARXI|ЦЕНА\s+ДОГОВОРА|СТОИМОСТЬ)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:NARX\s+VA\s+TO['']LOV|ЦЕНА\s+И\s+ПОРЯДОК\s+РАСЧЕТОВ)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:TO['']LOV\s+TARTIBI|ПОРЯДОК\s+ОПЛАТЫ)",
        ],
        SectionType.DELIVERY: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:YETKAZIB\s+BERISH|ПОСТАВКА|ДОСТАВКА)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:TOPSHIRISH\s+TARTIBI|ПОРЯДОК\s+СДАЧИ)",
        ],
        SectionType.QUALITY: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:SIFAT\s+TALABLARI|ТРЕБОВАНИЯ\s+К\s+КАЧЕСТВУ|Sifat)",
        ],
        SectionType.WARRANTY: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:KAFOLAT|ГАРАНТИЯ|ГАРАНТИЙНЫЕ)",
        ],
        SectionType.LIABILITY: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:JAVOBGARLIK|ОТВЕТСТВЕННОСТЬ)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:MODDIY\s+JAVOBGARLIK|МАТЕРИАЛЬНАЯ\s+ОТВЕТСТВЕННОСТЬ)",
        ],
        SectionType.FORCE_MAJEURE: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:FORS-MAJOR|ФОРС-МАЖОР|Favqulodda\s+holatlar)",
        ],
        SectionType.DISPUTE: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:NIZOLARNI\s+HAL\s+QILISH|РАЗРЕШЕНИЕ\s+СПОРОВ|Nizolar)",
        ],
        SectionType.TERM: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:SHARTNOMA\s+MUDDATI|СРОК\s+ДЕЙСТВИЯ|СРОК\s+ДОГОВОРА)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:AMAL\s+QILISH\s+MUDDATI)",
        ],
        SectionType.TERMINATION: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:SHARTNOMANI\s+BEKOR\s+QILISH|РАСТОРЖЕНИЕ\s+ДОГОВОРА)",
        ],
        SectionType.CONFIDENTIAL: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:MAXFIYLIK|КОНФИДЕНЦИАЛЬНОСТЬ)",
        ],
        SectionType.ADDITIONAL: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:QO['']SHIMCHA\s+SHARTLAR|ДОПОЛНИТЕЛЬНЫЕ\s+УСЛОВИЯ)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:BOSHQA\s+SHARTLAR|ПРОЧИЕ\s+УСЛОВИЯ)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:YAKUNIY\s+QOIDALAR|ЗАКЛЮЧИТЕЛЬНЫЕ\s+ПОЛОЖЕНИЯ)",
        ],
        SectionType.REQUISITES: [
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:TOMONLARNING\s+REKVIZITLARI|РЕКВИЗИТЫ\s+СТОРОН)",
            r"(?i)(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:YURIDIK\s+MANZILLAR|ЮРИДИЧЕСКИЕ\s+АДРЕСА)",
        ],
        SectionType.SIGNATURES: [
            r"(?i)(?:^|\n)\s*(?:IMZOLAR|ПОДПИСИ\s+СТОРОН)",
            r"(?i)M\.O['']\..*M\.O['']",  # M.O'. pattern for stamps
        ],
    }
    
    # Metadata extraction patterns
    METADATA_PATTERNS = {
        'contract_number': [
            r"(?i)№\s*([A-Za-z0-9\-/]+)",
            r"(?i)shartnoma\s*№?\s*([A-Za-z0-9\-/]+)",
            r"(?i)договор\s*№?\s*([A-Za-z0-9\-/]+)",
        ],
        'contract_date': [
            r"(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})",
            r"(\d{1,2})\s+(yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|oktabr|noyabr|dekabr)\s+(\d{4})",
            r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})",
        ],
        'inn': [
            r"(?i)(?:INN|ИНН|STIR)[:\s]*(\d{9})",
        ],
        'amount': [
            r"(?i)(\d[\d\s]*[\.,]?\d*)\s*(?:so['']m|сум|UZS|USD|\$)",
            r"(?i)jami\s*[:=]?\s*(\d[\d\s]*[\.,]?\d*)",
            r"(?i)итого\s*[:=]?\s*(\d[\d\s]*[\.,]?\d*)",
        ],
    }
    PARTY_PATTERNS = {
        'party_a_name': [
            r"(?im)(?:1[-\s]?tomon|birinchi\s+tomon|buyurtmachi|zakazchik|заказчик)[\s:–-]+(.+?)(?=\n|$)",
            r"(?im)taraflar\s*\(birinchi\s+tomoni\)[:\s]+(.+?)(?=\n|$)",
        ],
        'party_b_name': [
            r"(?im)(?:2[-\s]?tomon|ikkinchi\s+tomon|ijrochi|pudratchi|podryadchik|исполнитель)[\s:–-]+(.+?)(?=\n|$)",
            r"(?im)taraflar\s*\(ikkinchi\s+tomoni\)[:\s]+(.+?)(?=\n|$)",
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
        
        # Extract INNs
        inn_matches = re.findall(self.METADATA_PATTERNS['inn'][0], text)
        if len(inn_matches) >= 1:
            metadata.party_a_inn = inn_matches[0]
        if len(inn_matches) >= 2:
            metadata.party_b_inn = inn_matches[1]
        
        # Extract amount
        for pattern in self.METADATA_PATTERNS['amount']:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(' ', '').replace(',', '.')
                metadata.total_amount = amount_str
                break
        
        # Detect currency
        if 'USD' in text.upper() or '$' in text:
            metadata.currency = 'USD'
        elif 'EUR' in text.upper() or '€' in text:
            metadata.currency = 'EUR'
        else:
            metadata.currency = 'UZS'
        
        # Detect language
        metadata.language = self._detect_language(text)
        
        metadata.party_a_name = self._extract_party(text, 'party_a_name')
        metadata.party_b_name = self._extract_party(text, 'party_b_name')

        return metadata

    def _extract_party(self, text: str, field: str) -> Optional[str]:
        """Extract party name using defined patterns."""
        for pattern in self.PARTY_PATTERNS.get(field, []):
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None
    
    def _detect_language(self, text: str) -> str:
        """Detect contract language."""
        cyrillic = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        russian_specific = set('ъыэё')
        uzbek_specific = set("ғҳқўшчђҷ")
        
        cyrillic_count = sum(1 for c in text if c in cyrillic)
        russian_count = sum(1 for c in text if c in russian_specific)
        total_letters = sum(1 for c in text if c.isalpha())
        
        if total_letters == 0:
            return 'uz-latn'
        
        cyrillic_ratio = cyrillic_count / total_letters
        
        if cyrillic_ratio > 0.5:
            # prefer Uzbek Cyrillic if Uzbek-specific letters are present
            uzbek_indicator = sum(1 for c in text if c in uzbek_specific)
            if uzbek_indicator >= 2:
                return 'uz-cyrl'
            if russian_count > 10 and uzbek_indicator == 0:
                return 'ru'
            return 'uz-cyrl'
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
        
        # Sort by position
        positions.sort(key=lambda x: x[0])
        
        # Remove duplicates (same position, keep first)
        unique_positions = []
        last_pos = -100
        for pos in positions:
            if pos[0] - last_pos > 50:  # At least 50 chars apart
                unique_positions.append(pos)
                last_pos = pos[0]
        
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
