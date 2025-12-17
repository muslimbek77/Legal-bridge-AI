"""
Main Analysis Pipeline.
Orchestrates all AI components for complete contract analysis.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ai_engine.ocr import OCRProcessor
from ai_engine.parser import ContractParser, Section, ContractMetadata, SectionType
from ai_engine.compliance import LegalComplianceEngine, ComplianceIssue, IssueSeverity, IssueType
from ai_engine.risk_scoring import RiskScoringEngine, RiskScore
from ai_engine.rag import LegalRAG
from ai_engine.spelling import SpellingChecker, SpellingError

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analysis pipeline."""
    analyze_compliance: bool = True
    analyze_risks: bool = True
    analyze_spelling: bool = True  # Imloviy xatolarni tekshirish
    use_llm: bool = True
    use_rag: bool = True
    ocr_languages: List[str] = None
    llm_model: str = "llama3.1"
    
    def __post_init__(self):
        if self.ocr_languages is None:
            self.ocr_languages = ['uzb', 'uzb_latn', 'rus']


class ContractAnalysisPipeline:
    """
    Main pipeline for contract analysis.
    Integrates OCR, parsing, compliance checking, and risk scoring.
    """
    
    def __init__(self, config: AnalysisConfig = None):
        """
        Initialize the analysis pipeline.
        
        Args:
            config: Analysis configuration
        """
        self.config = config or AnalysisConfig()
        
        # Initialize components
        self.ocr = OCRProcessor(languages=self.config.ocr_languages)
        self.parser = ContractParser()
        self.compliance_engine = LegalComplianceEngine()
        self.risk_engine = RiskScoringEngine()
        self.spelling_checker = SpellingChecker()
        
        # RAG system (lazy initialization)
        self._rag = None
    
    @property
    def rag(self) -> LegalRAG:
        """Lazy initialization of RAG system."""
        if self._rag is None and self.config.use_rag:
            import os
            # Check if we should use OpenAI (if Ollama is not available)
            use_openai = bool(os.environ.get('OPENAI_API_KEY'))
            self._rag = LegalRAG(
                llm_model=self.config.llm_model,
                use_openai=use_openai,
                openai_model="gpt-3.5-turbo"
            )
            try:
                self._rag.initialize()
            except Exception as e:
                logger.warning(f"RAG initialization failed: {e}")
                self._rag = None
        return self._rag
    
    def analyze(self, contract) -> Dict[str, Any]:
        """
        Perform complete analysis on a contract.
        
        Args:
            contract: Contract model instance from Django
            
        Returns:
            Analysis results dictionary
        """
        start_time = time.time()
        
        try:
            # Step 1: Extract text
            logger.info(f"Starting analysis for contract: {contract.id}")
            text, ocr_confidence, is_scanned = self._extract_text(contract)
            
            # Update contract with extracted text
            contract.extracted_text = text
            contract.is_scanned = is_scanned
            contract.ocr_confidence = ocr_confidence
            contract.save()
            
            # Step 2: Parse contract
            logger.info("Parsing contract structure...")
            sections, metadata = self.parser.parse(text)
            
            # Step 3: Detect contract type
            contract_type = self._detect_contract_type(text, metadata)
            
            # Check if document is a valid contract
            is_valid_contract = self._is_valid_contract(text, metadata, contract_type)
            
            # Update contract metadata
            self._update_contract_metadata(contract, metadata, contract_type)
            
            # Step 4: Create sections in database
            self._save_sections(contract, sections)
            
            # If not a valid contract, only check spelling and return early
            if not is_valid_contract:
                logger.warning("Document is not a valid contract, skipping deep analysis")
                
                # Only check spelling errors
                spelling_errors = []
                issues = []
                if self.config.analyze_spelling:
                    logger.info("Checking spelling errors only...")
                    spelling_errors = self.spelling_checker.check_text(text, metadata.language)
                    for sp_error in spelling_errors:
                        issues.append(ComplianceIssue(
                            issue_type=IssueType.SPELLING,
                            severity=IssueSeverity.LOW,
                            title=f"Imloviy xato: {sp_error.word}",
                            description=sp_error.description,
                            section_reference=f"{sp_error.line_number}-qator",
                            clause_reference='',
                            text_excerpt=sp_error.context,
                            law_name='',
                            law_article='',
                            suggestion=f"To'g'ri yozilishi: {sp_error.suggestion}",
                            suggested_text=sp_error.suggestion
                        ))
                
                # Add warning about invalid contract
                issues.append(ComplianceIssue(
                    issue_type=IssueType.STRUCTURAL,
                    severity=IssueSeverity.CRITICAL,
                    title="Hujjat shartnoma emas",
                    description="Yuklangan hujjat hech qaysi shartnoma turiga to'g'ri kelmaydi. "
                               "Iltimos, to'g'ri shartnoma hujjatini yuklang.",
                    section_reference='',
                    clause_reference='',
                    text_excerpt=text[:500] if len(text) > 500 else text,
                    law_name='',
                    law_article='',
                    suggestion="Shartnoma hujjati quyidagi elementlarni o'z ichiga olishi kerak: "
                              "tomonlar, shartnoma predmeti, huquq va majburiyatlar, muddat, narx.",
                    suggested_text=''
                ))
                
                processing_time = time.time() - start_time
                
                return {
                    'success': True,
                    'contract_id': str(contract.id),
                    'contract_type': 'invalid',
                    'language': metadata.language,
                    'is_scanned': is_scanned,
                    'ocr_confidence': ocr_confidence,
                    'sections_count': len(sections),
                    'issues': [self._issue_to_dict(i) for i in issues],
                    'issues_count': len(issues),
                    'spelling_errors_count': len(spelling_errors),
                    'overall_score': 0,
                    'risk_level': 'critical',
                    'compliance_score': 0,
                    'completeness_score': 0,
                    'clarity_score': 0,
                    'balance_score': 0,
                    'summary': "⚠️ Yuklangan hujjat shartnoma emas yoki shartnoma formatiga to'g'ri kelmaydi. "
                              "Chuqur tahlil amalga oshirilmadi. "
                              f"Aniqlangan imloviy xatolar soni: {len(spelling_errors)}",
                    'recommendations': [
                        "To'g'ri shartnoma hujjatini yuklang",
                        "Shartnoma quyidagi turlardan biri bo'lishi kerak: xizmat ko'rsatish, mol yetkazib berish, pudrat, mehnat, ijara, davlat xaridi, qarz",
                        "Shartnomada tomonlar, muddat, narx va boshqa majburiy elementlar bo'lishi kerak"
                    ],
                    'enhanced_analysis': {},
                    'processing_time': processing_time,
                    'model_used': self.config.llm_model,
                    'is_valid_contract': False
                }
            
            # Step 5: Check compliance (only for valid contracts)
            issues = []
            if self.config.analyze_compliance:
                logger.info("Checking legal compliance...")
                issues = self.compliance_engine.check_compliance(
                    sections, metadata, contract_type
                )
            
            # Step 5.5: Check spelling errors
            spelling_errors = []
            if self.config.analyze_spelling:
                logger.info("Checking spelling errors...")
                spelling_errors = self.spelling_checker.check_text(text, metadata.language)
                # Convert spelling errors to compliance issues
                for sp_error in spelling_errors:
                    issues.append(ComplianceIssue(
                        issue_type=IssueType.SPELLING,
                        severity=IssueSeverity.LOW,
                        title=f"Imloviy xato: {sp_error.word}",
                        description=sp_error.description,
                        section_reference=f"{sp_error.line_number}-qator",
                        clause_reference='',
                        text_excerpt=sp_error.context,
                        law_name='',
                        law_article='',
                        suggestion=f"To'g'ri yozilishi: {sp_error.suggestion}",
                        suggested_text=sp_error.suggestion
                    ))
            
            # Step 6: Calculate risk score
            risk_score = None
            if self.config.analyze_risks:
                logger.info("Calculating risk score...")
                risk_score = self.risk_engine.calculate_score(
                    sections, metadata, issues, contract_type
                )
            
            # Step 7: Enhanced analysis with RAG (if available)
            enhanced_analysis = {}
            if self.config.use_rag and self.rag:
                logger.info("Running enhanced RAG analysis...")
                enhanced_analysis = self._run_rag_analysis(text, sections, contract_type)
            
            # Step 8: Generate summary
            summary = self._generate_summary(sections, metadata, issues, risk_score)
            
            # Compile results
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'contract_id': str(contract.id),
                'contract_type': contract_type,
                'language': metadata.language,
                'is_scanned': is_scanned,
                'ocr_confidence': ocr_confidence,
                'sections_count': len(sections),
                'issues': [self._issue_to_dict(i) for i in issues],
                'issues_count': len(issues),
                'spelling_errors_count': len(spelling_errors),
                'overall_score': risk_score.overall_score if risk_score else 50,
                'risk_level': risk_score.risk_level.value if risk_score else 'medium',
                'compliance_score': risk_score.compliance_score if risk_score else 50,
                'completeness_score': risk_score.completeness_score if risk_score else 50,
                'clarity_score': risk_score.clarity_score if risk_score else 50,
                'balance_score': risk_score.balance_score if risk_score else 50,
                'summary': summary,
                'recommendations': risk_score.recommendations if risk_score else [],
                'enhanced_analysis': enhanced_analysis,
                'processing_time': processing_time,
                'model_used': self.config.llm_model,
                'is_valid_contract': True,
            }
            
            logger.info(f"Analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
            }
    
    def _extract_text(self, contract) -> tuple:
        """Extract text from contract file."""
        file_path = contract.original_file.path
        return self.ocr.extract_text_from_file(file_path)
    
    def _detect_contract_type(self, text: str, metadata: ContractMetadata) -> str:
        """Detect contract type from text."""
        text_lower = text.lower()
        
        # Detection patterns
        type_patterns = {
            'service': [
                'xizmat ko\'rsatish', 'оказание услуг', 'xizmatlar',
                'услуги', 'сервис'
            ],
            'supply': [
                'mol yetkazib berish', 'поставка', 'yetkazib berish',
                'mahsulot yetkazish', 'товар'
            ],
            'work': [
                'pudrat', 'подряд', 'qurilish', 'ta\'mirlash',
                'строительство', 'ремонт'
            ],
            'labor': [
                'mehnat shartnomasi', 'трудовой договор', 'ish haqi',
                'заработная плата', 'xodim'
            ],
            'lease': [
                'ijara', 'аренда', 'ijaraga berish', 'ijaraga olish'
            ],
            'procurement': [
                'davlat xaridi', 'государственная закупка', 'tender',
                'тендер', 'konkurs'
            ],
            'loan': [
                'qarz', 'займ', 'кредит', 'kredit', 'ssuda'
            ],
        }
        
        scores = {ctype: 0 for ctype in type_patterns}
        
        for ctype, patterns in type_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    scores[ctype] += 1
        
        # Get type with highest score
        best_type = max(scores.items(), key=lambda x: x[1])
        
        if best_type[1] > 0:
            return best_type[0]
        
        return 'other'
    
    def _is_valid_contract(self, text: str, metadata: ContractMetadata, contract_type: str) -> bool:
        """
        Check if the document is a valid contract.
        Returns False if document doesn't match any contract type.
        """
        text_lower = text.lower()
        
        # If contract type is 'other', check for basic contract elements
        if contract_type == 'other':
            # Check for basic contract keywords
            contract_keywords = [
                'shartnoma', 'договор', 'kelishuv', 'соглашение',
                'bitim', 'контракт', 'kontrakt'
            ]
            
            has_contract_keyword = any(kw in text_lower for kw in contract_keywords)
            
            # Check for party indicators
            party_keywords = [
                'buyurtmachi', 'заказчик', 'pudratchi', 'подрядчик',
                'ijara beruvchi', 'арендодатель', 'ijara oluvchi', 'арендатор',
                'sotuvchi', 'продавец', 'xaridor', 'покупатель',
                'ish beruvchi', 'работодатель', 'xodim', 'работник',
                'tomon', 'сторона', '1-tomon', '2-tomon'
            ]
            
            has_parties = any(kw in text_lower for kw in party_keywords)
            
            # Check for legal elements
            legal_keywords = [
                'muddat', 'срок', 'narx', 'цена', 'summa', 'сумма',
                'majburiyat', 'обязательство', 'huquq', 'право',
                'javobgarlik', 'ответственность', 'imzo', 'подпись'
            ]
            
            has_legal_elements = sum(1 for kw in legal_keywords if kw in text_lower) >= 2
            
            # Document is valid contract if it has contract keyword AND (parties OR legal elements)
            return has_contract_keyword and (has_parties or has_legal_elements)
        
        # If contract type is detected, it's valid
        return True
    
    def _update_contract_metadata(self, contract, metadata: ContractMetadata, contract_type: str):
        """Update contract with extracted metadata."""
        if metadata.contract_number and not contract.contract_number:
            contract.contract_number = metadata.contract_number
        
        if metadata.party_a_name:
            contract.party_a = metadata.party_a_name
        if metadata.party_a_inn:
            contract.party_a_inn = metadata.party_a_inn
        
        if metadata.party_b_name:
            contract.party_b = metadata.party_b_name
        if metadata.party_b_inn:
            contract.party_b_inn = metadata.party_b_inn
        
        if metadata.total_amount:
            try:
                contract.total_amount = float(metadata.total_amount.replace(' ', ''))
            except:
                pass
        
        if metadata.currency:
            if metadata.currency:
                contract.currency = metadata.currency
        
            from apps.contracts.models import Contract as ContractModel

            language_defaults = {
                ContractModel.Language.UZ_LATN,
                ContractModel.Language.MIXED,
                '',
            }
            if metadata.language and contract.language in language_defaults:
                contract.language = metadata.language
        
            contract_type_defaults = {
                ContractModel.ContractType.OTHER,
                '',
            }
            if contract_type and contract.contract_type in contract_type_defaults:
                contract.contract_type = contract_type
        
            contract.save()
    
    def _save_sections(self, contract, sections: List[Section]):
        """Save parsed sections to database."""
        from apps.contracts.models import ContractSection, ContractClause
        
        # Clear existing sections
        ContractSection.objects.filter(contract=contract).delete()
        
        for i, section in enumerate(sections):
            db_section = ContractSection.objects.create(
                contract=contract,
                section_type=section.section_type.value,
                section_number=section.number,
                title=section.title,
                content=section.content,
                start_position=section.start_pos,
                end_position=section.end_pos,
                order=i
            )
            
            # Save clauses
            for j, clause in enumerate(section.clauses):
                ContractClause.objects.create(
                    section=db_section,
                    clause_number=clause.number,
                    content=clause.content,
                    order=j
                )
    
    def _run_rag_analysis(self, text: str, sections: List[Section], contract_type: str) -> Dict:
        """Run enhanced analysis using RAG."""
        results = {}
        
        try:
            # Find relevant laws
            relevant_laws = self.rag.search_laws(
                text[:2000],  # Use first 2000 chars for search
                contract_type,
                n_results=10
            )
            results['relevant_laws'] = relevant_laws
            
            # Analyze key sections
            key_sections = [SectionType.SUBJECT, SectionType.LIABILITY, SectionType.PRICE]
            section_analyses = {}
            
            for section in sections:
                if section.section_type in key_sections:
                    analysis = self.rag.analyze_clause(
                        section.content[:1000],
                        contract_type
                    )
                    section_analyses[section.section_type.value] = analysis.get('analysis', '')
            
            results['section_analyses'] = section_analyses
            
        except Exception as e:
            logger.error(f"RAG analysis failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def _generate_summary(
        self,
        sections: List[Section],
        metadata: ContractMetadata,
        issues: List[ComplianceIssue],
        risk_score: Optional[RiskScore]
    ) -> str:
        """Generate analysis summary."""
        summary_parts = []
        
        # Contract overview
        summary_parts.append(f"Shartnoma tahlili yakunlandi.")
        summary_parts.append(f"Til: {metadata.language}")
        summary_parts.append(f"Bo'limlar soni: {len(sections)}")
        
        # Issues summary
        if issues:
            critical_count = sum(1 for i in issues if i.severity.value == 'critical')
            high_count = sum(1 for i in issues if i.severity.value == 'high')
            
            summary_parts.append(f"\nAniqlangan muammolar: {len(issues)}")
            if critical_count:
                summary_parts.append(f"- Jiddiy: {critical_count}")
            if high_count:
                summary_parts.append(f"- Yuqori: {high_count}")
        else:
            summary_parts.append("\nMuammolar topilmadi.")
        
        # Risk score summary
        if risk_score:
            level_text = {
                'low': "past (qonunga mos)",
                'medium': "o'rta (takomillashtirish kerak)",
                'high': "yuqori (jiddiy muammolar bor)"
            }
            summary_parts.append(
                f"\nXavf darajasi: {risk_score.overall_score}/100 - {level_text.get(risk_score.risk_level.value, '')}"
            )
        
        return "\n".join(summary_parts)
    
    def _issue_to_dict(self, issue: ComplianceIssue) -> Dict:
        """Convert ComplianceIssue to dictionary."""
        return {
            'type': issue.issue_type.value,
            'severity': issue.severity.value,
            'title': issue.title,
            'description': issue.description,
            'section': issue.section_reference,
            'clause': issue.clause_reference,
            'text_excerpt': issue.text_excerpt,
            'law_name': issue.law_name,
            'law_article': issue.law_article,
            'suggestion': issue.suggestion,
            'suggested_text': issue.suggested_text,
        }
    
    def analyze_text(self, text: str, contract_type: str = 'other') -> Dict[str, Any]:
        """
        Analyze contract text directly (without file).
        Useful for testing and API usage.
        """
        start_time = time.time()
        
        try:
            # Parse contract
            sections, metadata = self.parser.parse(text)
            
            # Detect type if not provided
            if contract_type == 'other':
                contract_type = self._detect_contract_type(text, metadata)
            
            # Check compliance
            issues = self.compliance_engine.check_compliance(
                sections, metadata, contract_type
            )
            
            # Calculate risk score
            risk_score = self.risk_engine.calculate_score(
                sections, metadata, issues, contract_type
            )
            
            # Generate summary
            summary = self._generate_summary(sections, metadata, issues, risk_score)
            
            return {
                'success': True,
                'contract_type': contract_type,
                'language': metadata.language,
                'metadata': {
                    'contract_number': metadata.contract_number,
                    'contract_date': metadata.contract_date,
                    'party_a_inn': metadata.party_a_inn,
                    'party_b_inn': metadata.party_b_inn,
                    'total_amount': metadata.total_amount,
                    'currency': metadata.currency,
                },
                'sections': [
                    {
                        'type': s.section_type.value,
                        'title': s.title,
                        'clauses_count': len(s.clauses)
                    }
                    for s in sections
                ],
                'issues': [self._issue_to_dict(i) for i in issues],
                'risk_score': {
                    'overall': risk_score.overall_score,
                    'level': risk_score.risk_level.value,
                    'compliance': risk_score.compliance_score,
                    'completeness': risk_score.completeness_score,
                    'clarity': risk_score.clarity_score,
                    'balance': risk_score.balance_score,
                },
                'recommendations': risk_score.recommendations,
                'summary': summary,
                'processing_time': time.time() - start_time,
            }
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
            }
