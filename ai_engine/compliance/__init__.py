"""
Legal Compliance Engine.
Checks contracts against Uzbekistan laws and regulations.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ai_engine.parser import Section, SectionType, ContractMetadata

logger = logging.getLogger(__name__)


# O'zbekcha termin tarjimalari
SECTION_NAMES_UZ = {
    "parties": "Tomonlar",
    "subject": "Shartnoma predmeti",
    "price": "Narx va to'lov shartlari",
    "term": "Shartnoma muddati",
    "liability": "Javobgarlik",
    "requisites": "Tomonlar rekvizitlari",
    "delivery": "Yetkazib berish shartlari",
    "quality": "Sifat talablari",
    "warranty": "Kafolat",
    "force_majeure": "Fors-major",
    "dispute": "Nizolarni hal qilish",
    "termination": "Shartnomani bekor qilish",
    "rights": "Huquqlar",
    "obligations": "Majburiyatlar",
    "signatures": "Imzolar",
    "confidentiality": "Maxfiylik",
    "amendments": "O'zgartirishlar",
    "acceptance": "Qabul qilish",
    "payment": "To'lov",
    "other": "Boshqa",
}


def get_section_name_uz(section_value: str) -> str:
    """Get Uzbek name for section type."""
    return SECTION_NAMES_UZ.get(section_value, section_value)


class IssueSeverity(Enum):
    """Severity levels for compliance issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Types of compliance issues."""
    MISSING_CLAUSE = "missing_clause"
    INVALID_CLAUSE = "invalid_clause"
    ONE_SIDED = "one_sided"
    UNCLEAR = "unclear"
    CONFLICT = "conflict"
    ILLEGAL = "illegal"
    MISSING_INFO = "missing_info"
    FORMAT = "format"
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    STRUCTURAL = "structural"  # Document structure issues
    INVALID_DOCUMENT = "invalid_document"  # Not a valid contract
    OTHER = "other"


@dataclass
class ComplianceIssue:
    """Represents a compliance issue found in contract."""
    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    section_reference: str = ""
    clause_reference: str = ""
    text_excerpt: str = ""
    law_name: str = ""
    law_article: str = ""
    law_text: str = ""
    suggestion: str = ""
    suggested_text: str = ""


@dataclass
class LegalRule:
    """Represents a legal rule for contract validation."""
    rule_id: str
    title: str
    description: str
    law_name: str
    law_article: str
    applies_to: List[str]  # Contract types
    section_type: Optional[SectionType]
    severity: IssueSeverity
    check_type: str  # "mandatory", "prohibited", "format", etc.
    keywords: List[str] = field(default_factory=list)
    validation_func: Optional[str] = None


class LegalComplianceEngine:
    """
    Engine for checking contract compliance with Uzbekistan laws.
    """
    
    # Required sections by contract type
    REQUIRED_SECTIONS = {
        "service": [
            SectionType.PARTIES,
            SectionType.SUBJECT,
            SectionType.PRICE,
            SectionType.TERM,
            SectionType.LIABILITY,
            SectionType.REQUISITES,
        ],
        "supply": [
            SectionType.PARTIES,
            SectionType.SUBJECT,
            SectionType.PRICE,
            SectionType.DELIVERY,
            SectionType.QUALITY,
            SectionType.WARRANTY,
            SectionType.LIABILITY,
            SectionType.REQUISITES,
        ],
        "work": [
            SectionType.PARTIES,
            SectionType.SUBJECT,
            SectionType.PRICE,
            SectionType.TERM,
            SectionType.QUALITY,
            SectionType.LIABILITY,
            SectionType.REQUISITES,
        ],
        "labor": [
            SectionType.PARTIES,
            SectionType.SUBJECT,
            SectionType.RIGHTS,
            SectionType.OBLIGATIONS,
            SectionType.PRICE,  # Salary
            SectionType.TERM,
            SectionType.LIABILITY,
        ],
        "lease": [
            SectionType.PARTIES,
            SectionType.SUBJECT,
            SectionType.PRICE,
            SectionType.TERM,
            SectionType.RIGHTS,
            SectionType.OBLIGATIONS,
            SectionType.LIABILITY,
            SectionType.REQUISITES,
        ],
        "procurement": [
            SectionType.PARTIES,
            SectionType.SUBJECT,
            SectionType.PRICE,
            SectionType.DELIVERY,
            SectionType.QUALITY,
            SectionType.WARRANTY,
            SectionType.LIABILITY,
            SectionType.FORCE_MAJEURE,
            SectionType.DISPUTE,
            SectionType.REQUISITES,
        ],
    }
    
    # Built-in legal rules based on Uzbekistan Civil Code
    LEGAL_RULES = [
        # General contract requirements (FQ 354-modda)
        LegalRule(
            rule_id="FK_354_1",
            title="Shartnoma predmeti majburiy",
            description="Shartnomada predmet (mavzu) aniq ko'rsatilishi shart",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="354-modda",
            applies_to=["all"],
            section_type=SectionType.SUBJECT,
            severity=IssueSeverity.CRITICAL,
            check_type="mandatory",
            keywords=["predmet", "mavzu", "предмет"],
        ),
        
        # Party identification (FQ 355-modda)
        LegalRule(
            rule_id="FK_355_1",
            title="Tomonlar to'liq ko'rsatilishi shart",
            description="Shartnoma tomonlarining to'liq nomi, manzili va rekvizitlari ko'rsatilishi kerak",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="355-modda",
            applies_to=["all"],
            section_type=SectionType.PARTIES,
            severity=IssueSeverity.CRITICAL,
            check_type="mandatory",
            keywords=["tomon", "buyurtmachi", "ijrochi", "заказчик", "исполнитель"],
        ),
        
        # Price terms (FQ 356-modda)
        LegalRule(
            rule_id="FK_356_1",
            title="Narx sharti",
            description="Shartnomada narx yoki narxni aniqlash tartibi ko'rsatilishi kerak",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="356-modda",
            applies_to=["all"],
            section_type=SectionType.PRICE,
            severity=IssueSeverity.HIGH,
            check_type="mandatory",
            keywords=["narx", "summa", "to'lov", "цена", "стоимость", "оплата"],
        ),
        
        # Contract term (FQ 357-modda)
        LegalRule(
            rule_id="FK_357_1",
            title="Shartnoma muddati",
            description="Shartnomaning amal qilish muddati belgilanishi kerak",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="357-modda",
            applies_to=["all"],
            section_type=SectionType.TERM,
            severity=IssueSeverity.HIGH,
            check_type="mandatory",
            keywords=["muddat", "срок", "дата", "sana"],
        ),
        
        # Liability limits (FQ 325-modda)
        LegalRule(
            rule_id="FK_325_1",
            title="Javobgarlikni cheklash",
            description="Qasddan yetkazilgan zarar uchun javobgarlikni oldindan cheklash mumkin emas",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="325-modda",
            applies_to=["all"],
            section_type=SectionType.LIABILITY,
            severity=IssueSeverity.CRITICAL,
            check_type="prohibited",
            keywords=["javobgarlikdan ozod", "освобождение от ответственности"],
        ),
        
        # Warranty for goods (FQ 417-modda)
        LegalRule(
            rule_id="FK_417_1",
            title="Mol sifati kafolati",
            description="Mol yetkazib berish shartnomalarida kafolat muddati ko'rsatilishi kerak",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="417-modda",
            applies_to=["supply"],
            section_type=SectionType.WARRANTY,
            severity=IssueSeverity.HIGH,
            check_type="mandatory",
            keywords=["kafolat", "гарантия", "sifat", "качество"],
        ),
        
        # Force majeure (FQ 333-modda)
        LegalRule(
            rule_id="FK_333_1",
            title="Fors-major holatlari",
            description="Fors-major holatlari va ularning oqibatlari belgilanishi tavsiya etiladi",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="333-modda",
            applies_to=["supply", "work", "procurement"],
            section_type=SectionType.FORCE_MAJEURE,
            severity=IssueSeverity.MEDIUM,
            check_type="recommended",
            keywords=["fors-major", "форс-мажор", "favqulodda"],
        ),
        
        # Penalty limits (FQ 327-modda)
        LegalRule(
            rule_id="FK_327_1",
            title="Penya miqdori",
            description="Penya miqdori asosiy qarzdan oshmasligi kerak (ayrim holatlar bundan mustasno)",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="327-modda",
            applies_to=["all"],
            section_type=SectionType.LIABILITY,
            severity=IssueSeverity.HIGH,
            check_type="limit",
            keywords=["penya", "пеня", "jarima", "штраф", "neustoyka"],
        ),
        
        # State procurement requirements
        LegalRule(
            rule_id="DX_2021_1",
            title="Davlat xaridi majburiy shartlari",
            description="Davlat xaridlari shartnomalarida maxsus talablar bajarilishi shart",
            law_name="Davlat xaridlari to'g'risida qonun",
            law_article="25-modda",
            applies_to=["procurement"],
            section_type=None,
            severity=IssueSeverity.CRITICAL,
            check_type="format",
            keywords=["davlat xaridi", "государственная закупка", "tender"],
        ),
        
        # Labor contract requirements
        LegalRule(
            rule_id="MK_72_1",
            title="Mehnat shartnomasi majburiy shartlari",
            description="Mehnat shartnomasi ish joyi, lavozim, ish haqi va ish vaqtini o'z ichiga olishi kerak",
            law_name="O'zbekiston Respublikasi Mehnat kodeksi",
            law_article="72-modda",
            applies_to=["labor"],
            section_type=SectionType.SUBJECT,
            severity=IssueSeverity.CRITICAL,
            check_type="mandatory",
            keywords=["mehnat", "труд", "ish haqi", "заработная плата"],
        ),
        
        # Written form requirement (FQ 107-modda)
        LegalRule(
            rule_id="FK_107_1",
            title="Yozma shakl talabi",
            description="Yuridik shaxslar orasidagi shartnomalar yozma shaklda tuzilishi shart",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="107-modda",
            applies_to=["all"],
            section_type=SectionType.SIGNATURES,
            severity=IssueSeverity.CRITICAL,
            check_type="format",
            keywords=["imzo", "подпись", "muhr", "печать"],
        ),
        
        # Requisites requirement
        LegalRule(
            rule_id="FK_355_2",
            title="Bank rekvizitlari",
            description="Tomonlarning bank rekvizitlari to'liq ko'rsatilishi kerak",
            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
            law_article="355-modda",
            applies_to=["all"],
            section_type=SectionType.REQUISITES,
            severity=IssueSeverity.HIGH,
            check_type="mandatory",
            keywords=["bank", "hisob raqam", "расчетный счет", "р/с", "MFO"],
        ),
    ]
    
    def __init__(self, custom_rules: List[LegalRule] = None, template_rules: Dict = None):
        """
        Initialize the compliance engine.
        
        Args:
            custom_rules: Additional custom rules to add
            template_rules: Template-specific requirements from contract_templates.json
        """
        self.rules = self.LEGAL_RULES.copy()
        if custom_rules:
            self.rules.extend(custom_rules)
        
        # Template-specific rules
        self.template_rules = template_rules or {}
        self._add_template_rules()
    
    def _add_template_rules(self):
        """Add template-specific rules from contract_templates.json."""
        # Template tayyorga asoslangan qo'shimcha qoidalar
        template_specific_rules = {
            'employment': [
                LegalRule(
                    rule_id="EMPL_001",
                    title="Mehnat sharoitlari majburiy",
                    description="Mehnat shartnomalarida ish vaqti, dam olish kunlari va mehnat sharoitlari aniq ko'rsatilishi shart",
                    law_name="O'zbekiston Respublikasi Mehnat kodeksi",
                    law_article="27-modda",
                    applies_to=["labor"],
                    section_type=SectionType.OBLIGATIONS,
                    severity=IssueSeverity.HIGH,
                    check_type="mandatory",
                    keywords=["ish vaqti", "dam olish", "mehnat sharoitlari", "рабочее время", "отпуск"],
                ),
                LegalRule(
                    rule_id="EMPL_002",
                    title="Ijtimoiy kafolatlar",
                    description="Xodim ijtimoiy sug'urta va boshqa kafolatlar bilan ta'minlanishi kerak",
                    law_name="O'zbekiston Respublikasi Mehnat kodeksi",
                    law_article="72-modda",
                    applies_to=["labor"],
                    section_type=SectionType.RIGHTS,
                    severity=IssueSeverity.HIGH,
                    check_type="mandatory",
                    keywords=["ijtimoiy kafolat", "sug'urta", "социальные гарантии"],
                ),
            ],
            'lease': [
                LegalRule(
                    rule_id="LEASE_001",
                    title="Ko'chmas mulk ijara shartnomasi davlat ro'yxatidan o'tishi",
                    description="Ko'chmas mulkni ijaraga berishning shartnomasi davlat ro'yxatidan o'tkazilishi kerak",
                    law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
                    law_article="576-modda",
                    applies_to=["lease"],
                    section_type=None,
                    severity=IssueSeverity.HIGH,
                    check_type="mandatory",
                    keywords=["ro'yxat", "davlat", "регистрация"],
                ),
            ],
            'supply': [
                LegalRule(
                    rule_id="SUPPLY_001",
                    title="Mol sifatining kafolati",
                    description="Yetkazib berish shartnomalarida mol sifatining kafolati aniq ko'rsatilishi shart",
                    law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
                    law_article="450-modda",
                    applies_to=["supply"],
                    section_type=SectionType.WARRANTY,
                    severity=IssueSeverity.HIGH,
                    check_type="mandatory",
                    keywords=["kafolat", "sifat", "gарантия", "качество"],
                ),
            ],
        }
        
        # Har bir contract type uchun rules'ni qo'shish
        for contract_type, rules in template_specific_rules.items():
            self.rules.extend(rules)
    
    def check_compliance(
        self,
        sections: List[Section],
        metadata: ContractMetadata,
        contract_type: str = "other"
    ) -> List[ComplianceIssue]:
        """
        Check contract compliance against legal rules.
        
        Args:
            sections: Parsed contract sections
            metadata: Extracted metadata
            contract_type: Type of contract
            
        Returns:
            List of compliance issues found
        """
        issues = []
        
        # Check required sections
        issues.extend(self._check_required_sections(sections, contract_type))
        
        # Check each applicable rule
        applicable_rules = self._get_applicable_rules(contract_type)
        for rule in applicable_rules:
            rule_issues = self._check_rule(rule, sections, metadata)
            issues.extend(rule_issues)
        
        # Check for one-sided clauses
        issues.extend(self._check_balance(sections))
        
        # Check metadata completeness
        issues.extend(self._check_metadata(metadata, contract_type))
        
        # Check for risky clauses (rekurziv, bir tomonli, cheksiz javobgarlik, va h.k.)
        issues.extend(self.detect_risky_clauses(sections, contract_type))
        
        return issues
    
    def _get_applicable_rules(self, contract_type: str) -> List[LegalRule]:
        """Get rules applicable to a contract type."""
        applicable = []
        for rule in self.rules:
            if "all" in rule.applies_to or contract_type in rule.applies_to:
                applicable.append(rule)
        return applicable
    
    def _check_required_sections(self, sections: List[Section], contract_type: str) -> List[ComplianceIssue]:
        """Check if all required sections are present."""
        issues = []
        
        required = self.REQUIRED_SECTIONS.get(contract_type, self.REQUIRED_SECTIONS.get("service", []))
        found_types = {s.section_type for s in sections}
        
        # Check if requisites-like content exists anywhere in text (bank details, INN, etc)
        all_text = ' '.join(s.content.lower() for s in sections)
        has_requisites_content = any(kw in all_text for kw in ['stir', 'inn', 'банк', 'bank', 'р/с', 'мфо', 'mfo', 'расчетный счет', 'hisob raqam'])
        if has_requisites_content and SectionType.REQUISITES not in found_types:
            found_types.add(SectionType.REQUISITES)

        # Soft fallback: if strong keywords for a section appear in text, don't mark as missing
        section_fallback_keywords = {
            SectionType.SUBJECT: ['предмет', 'шартнома предмети', 'мавзу', 'мавзуси'],
            SectionType.PRICE: ['цена договора', 'цена', 'стоимость работ', 'стоимость', 'оплата', 'порядок расчетов', 'расчетов', 'нарх', "to'lov", 'tulov', 'тўлов', 'сумма', 'узс', 'uzs', 'қиймати', 'қиймати'],
            SectionType.TERM: ['срок действия', 'срок договора', 'срок выполнения', 'сроки выполнения', 'срок исполнения', 'срок', 'муддат', 'амал қилади', 'амал килади', 'действует', 'действует до', 'to kuni'],
            SectionType.LIABILITY: ['ответственность сторон', 'материальная ответственность', 'ответственность', 'javobgarlik', 'штраф', 'пеня', 'jarima'],
            SectionType.DELIVERY: ['поставка', 'доставка', 'yetkazib', 'етказиб'],
            SectionType.QUALITY: ['качество', 'сифат', 'sifat'],
            SectionType.WARRANTY: ['гарант', 'kafolat', 'кафолат'],
            SectionType.DISPUTE: ['спор', 'da’vo', 'nizo', 'низо'],
        }
        
        logger.info(f"[COMPLIANCE] required={required}, found={found_types}")
        
        # Treat strong keyword evidence as presence to improve completeness score
        for section_type in required:
            if section_type not in found_types:
                fallback_kws = section_fallback_keywords.get(section_type, [])
                if fallback_kws and any(kw in all_text for kw in fallback_kws):
                    found_types.add(section_type)
        
        for section_type in required:
            if section_type not in found_types:
                # If still missing and no evidence, then report
                fallback_kws = section_fallback_keywords.get(section_type, [])
                if fallback_kws and any(kw in all_text for kw in fallback_kws):
                    # Already counted as present above; skip
                    continue
                section_name_uz = get_section_name_uz(section_type.value)
                issues.append(ComplianceIssue(
                    issue_type=IssueType.MISSING_CLAUSE,
                    severity=IssueSeverity.HIGH,
                    title=f"Yetishmayotgan bo'lim: {section_name_uz}",
                    description=f"Shartnomada '{section_name_uz}' bo'limi topilmadi",
                    suggestion=f"'{section_name_uz}' bo'limini qo'shing",
                    law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
                    law_article="354-modda",
                ))
        
        return issues
    
    def _check_rule(
        self,
        rule: LegalRule,
        sections: List[Section],
        metadata: ContractMetadata
    ) -> List[ComplianceIssue]:
        """Check a single rule against the contract."""
        issues = []
        
        # Get relevant section
        if rule.section_type:
            section = self._get_section_by_type(sections, rule.section_type)
            section_name_uz = get_section_name_uz(rule.section_type.value)
            
            # For PRICE section, also check if metadata has amount (content may be in different section)
            if not section and rule.section_type == SectionType.PRICE and metadata.total_amount:
                return issues  # Price found in metadata, skip issue
            
            # For TERM section, check if term info exists anywhere in text
            if not section and rule.section_type == SectionType.TERM:
                all_text = ' '.join(s.content.lower() for s in sections)
                if any(kw in all_text for kw in ['amal qiladi', 'muddati', 'действует', 'срок']):
                    return issues  # Term info found in contract text
            
            if not section and rule.check_type == "mandatory":
                # Soft fallback: if keywords appear anywhere in text, treat as present
                all_text = ' '.join(s.content.lower() for s in sections)
                kw_anywhere = any(kw.lower() in all_text for kw in rule.keywords)
                if kw_anywhere or rule.section_type in {
                    SectionType.REQUISITES,
                    SectionType.TERM,
                    SectionType.PRICE,
                    SectionType.SUBJECT,
                }:
                    return issues
                issues.append(ComplianceIssue(
                    issue_type=IssueType.MISSING_CLAUSE,
                    severity=rule.severity,
                    title=rule.title,
                    description=rule.description,
                    law_name=rule.law_name,
                    law_article=rule.law_article,
                    suggestion=f"'{section_name_uz}' bo'limini qo'shing",
                ))
                return issues
            
            if section:
                # Check for keywords
                content_lower = section.content.lower()
                found_keywords = [kw for kw in rule.keywords if kw.lower() in content_lower]
                
                if rule.check_type == "mandatory" and not found_keywords:
                    # If the section exists but keywords aren't found, treat core structural sections as present
                    if rule.section_type in {
                        SectionType.SUBJECT,
                        SectionType.PARTIES,
                        SectionType.TERM,
                        SectionType.REQUISITES,
                        SectionType.PRICE,
                    }:
                        return issues
                    issues.append(ComplianceIssue(
                        issue_type=IssueType.MISSING_INFO,
                        severity=rule.severity,
                        title=rule.title,
                        description=rule.description,
                        section_reference=section.title,
                        law_name=rule.law_name,
                        law_article=rule.law_article,
                        suggestion=f"Ushbu ma'lumotlarni qo'shing: {', '.join(rule.keywords[:3])}",
                    ))
                
                elif rule.check_type == "prohibited":
                    for keyword in rule.keywords:
                        if keyword.lower() in content_lower:
                            # Find the problematic text
                            idx = content_lower.find(keyword.lower())
                            excerpt = section.content[max(0, idx-50):idx+len(keyword)+50]
                            
                            issues.append(ComplianceIssue(
                                issue_type=IssueType.ILLEGAL,
                                severity=rule.severity,
                                title=rule.title,
                                description=rule.description,
                                section_reference=section.title,
                                text_excerpt=excerpt,
                                law_name=rule.law_name,
                                law_article=rule.law_article,
                                suggestion="Bu bandni o'chirib tashlang yoki o'zgartiring",
                            ))
        
        return issues
    
    def _check_balance(self, sections: List[Section]) -> List[ComplianceIssue]:
        """Check for one-sided clauses."""
        issues = []
        
        # Keywords indicating one-sided clauses
        one_sided_patterns = [
            ("bir tomonlama bekor qilish", "Bir tomonlama bekor qilish huquqi"),
            ("односторонний отказ", "Bir tomonlama rad etish"),
            ("без согласия", "Rozilikisiz o'zgartirish"),
            ("faqat buyurtmachi", "Faqat bir tomonga berilgan huquq"),
            ("faqat ijrochi", "Faqat bir tomonga berilgan huquq"),
            ("только заказчик", "Faqat bir tomonga berilgan huquq"),
            ("только исполнитель", "Faqat bir tomonga berilgan huquq"),
        ]
        
        for section in sections:
            content_lower = section.content.lower()
            for pattern, description in one_sided_patterns:
                if pattern in content_lower:
                    idx = content_lower.find(pattern)
                    excerpt = section.content[max(0, idx-30):idx+len(pattern)+30]
                    
                    issues.append(ComplianceIssue(
                        issue_type=IssueType.ONE_SIDED,
                        severity=IssueSeverity.MEDIUM,
                        title=description,
                        description="Bu band bir tomonga ortiqcha ustunlik berishi mumkin",
                        section_reference=section.title,
                        text_excerpt=excerpt,
                        suggestion="Bandni ikkala tomon uchun muvozanatli qiling",
                    ))
        
        return issues
    
    def _check_metadata(self, metadata: ContractMetadata, contract_type: str) -> List[ComplianceIssue]:
        """Check metadata completeness."""
        issues = []
        
        if not metadata.contract_date:
            issues.append(ComplianceIssue(
                issue_type=IssueType.MISSING_INFO,
                severity=IssueSeverity.MEDIUM,  # Reduced from HIGH
                title="Shartnoma sanasi ko'rsatilmagan",
                description="Shartnoma tuzilgan sana aniqlanmadi",
                suggestion="Shartnoma sanasini aniq ko'rsating",
                law_name="Fuqarolik kodeksi",
                law_article="107-modda",
            ))
        
        if not metadata.party_a_inn:
            issues.append(ComplianceIssue(
                issue_type=IssueType.MISSING_INFO,
                severity=IssueSeverity.MEDIUM,  # Reduced from HIGH
                title="1-tomon INN/STIR ko'rsatilmagan",
                description="Birinchi tomonning identifikatsiya raqami topilmadi",
                suggestion="Tomonning INN/STIR raqamini qo'shing",
            ))
        
        if not metadata.party_b_inn:
            issues.append(ComplianceIssue(
                issue_type=IssueType.MISSING_INFO,
                severity=IssueSeverity.MEDIUM,  # Reduced from HIGH
                title="2-tomon INN/STIR ko'rsatilmagan",
                description="Ikkinchi tomonning identifikatsiya raqami topilmadi",
                suggestion="Tomonning INN/STIR raqamini qo'shing",
            ))
        
        if contract_type in ["supply", "service", "work", "procurement"]:
            if not metadata.total_amount:
                issues.append(ComplianceIssue(
                    issue_type=IssueType.MISSING_INFO,
                    severity=IssueSeverity.MEDIUM,  # Reduced from HIGH
                    title="Shartnoma summasi ko'rsatilmagan",
                    description="Shartnomaning umumiy summasi aniqlanmadi",
                    suggestion="Shartnoma summasini aniq ko'rsating",
                    law_name="Fuqarolik kodeksi",
                    law_article="356-modda",
                ))
        
        return issues
    
    def _get_section_by_type(self, sections: List[Section], section_type: SectionType) -> Optional[Section]:
        """Get section by type."""
        for section in sections:
            if section.section_type == section_type:
                return section
        return None
    
    def add_rule(self, rule: LegalRule):
        """Add a custom rule."""
        self.rules.append(rule)
    
    def get_rules_for_contract_type(self, contract_type: str) -> List[LegalRule]:
        """Get all rules applicable to a contract type."""
        return self._get_applicable_rules(contract_type)
    
    def detect_risky_clauses(self, sections: List[Section], contract_type: str) -> List[ComplianceIssue]:
        """
        Detect potentially risky clauses like recursive conditions,
        one-sided terms, illegal provisions, etc.
        
        UPDATED: More lenient, fewer false positives.
        """
        risky_issues = []
        
        # Xavfli naqsh-shablonlar (YUMSHATILGAN - faqat haqiqiy xavflar)
        risky_patterns = {
            'unlimited_liability': {
                'patterns': [
                    r'cheksiz\s+javobgarlik',
                    r'неограниченная\s+ответственность',
                    r'javobgarlikdan\s+to\'liq\s+ozod',  # Complete exemption
                    r'полностью\s+освобождается\s+от\s+ответственности',
                ],
                'severity': IssueSeverity.HIGH,  # Lowered from CRITICAL
                'title': 'Noaniq javobgarlik shartlari',
                'description': 'Javobgarlik shartlari aniqlanishi tavsiya etiladi',
            },
            'illegal_provision': {
                'patterns': [
                    r'qonunga\s+qarshi',
                    r'противозаконн',
                    r'запрещен',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Qonunga zid shart',
                'description': 'Shartnomada qonunga zid shart topildi',
            },
            'very_high_penalty': {
                'patterns': [
                    r'penya\s+([5-9]|[1-9]\d)%',  # 5% dan yuqori kunlik penya
                    r'пеня\s+([5-9]|[1-9]\d)%',
                ],
                'severity': IssueSeverity.MEDIUM,  # Lowered from HIGH
                'title': 'Yuqori penya miqdori',
                'description': 'Penya miqdori yuqori, qonun talablariga mos ekanligini tekshiring',
            },
        }
        
        # Hammasini qidirish (faqat haqiqatan xavfli narsalar)
        for section in sections:
            section_content = section.content.lower()
            
            for pattern_category, pattern_info in risky_patterns.items():
                for pattern in pattern_info['patterns']:
                    matches = list(re.finditer(pattern, section_content, re.IGNORECASE))
                    if matches:
                        # Faqat bitta xatolik har bir pattern category uchun
                        risky_issues.append(ComplianceIssue(
                            issue_type=IssueType.INVALID_CLAUSE,
                            severity=pattern_info['severity'],
                            title=pattern_info['title'],
                            description=pattern_info['description'],
                            section_reference=f"{section.section_type.value}",
                            clause_reference=section.title,
                            text_excerpt=section.content[:200],
                            law_name="O'zbekiston Respublikasi Fuqarolik kodeksi",
                            law_article="Umumiy talablar",
                            suggestion=f"Shartnomani yurist bilan ko'rib chiqing",
                        ))
                        break  # Har bir pattern category uchun faqat 1 ta xatolik
        
        return risky_issues

