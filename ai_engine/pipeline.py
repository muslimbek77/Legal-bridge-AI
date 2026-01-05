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
from ai_engine.risk_scoring import RiskScoringEngine, RiskScore, ClauseAnalysis
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
    use_gemini: bool = False
    ocr_languages: List[str] = None
    llm_model: str = "llama3.1"
    gemini_model: str = "gemini-flash-latest"
    
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
            # Check if we should use Gemini
            use_gemini = self.config.use_gemini or bool(os.environ.get('GEMINI_API_KEY'))
            
            # Force correct model name
            gemini_model = "gemini-flash-latest"
            logger.info(f"Initializing RAG with Gemini model: {gemini_model}")

            self._rag = LegalRAG(
                llm_model=self.config.llm_model,
                use_openai=use_openai,
                openai_model="gpt-3.5-turbo",
                use_gemini=use_gemini,
                gemini_model=gemini_model
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
        t_ocr = t_parse = t_spelling = t_compliance = t_risk = t_rag = 0.0
        
        try:
            # Step 1: Extract text
            logger.info(f"Starting analysis for contract: {contract.id}")
            _t0 = time.time()
            text, ocr_confidence, is_scanned = self._extract_text(contract)
            t_ocr = time.time() - _t0
            
            # Update contract with extracted text
            contract.extracted_text = text
            contract.is_scanned = is_scanned
            contract.ocr_confidence = ocr_confidence
            contract.save()
            
            # Step 2: Parse contract
            logger.info("Parsing contract structure...")
            _t0 = time.time()
            sections, metadata = self.parser.parse(text)
            t_parse = time.time() - _t0
            
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
                _t0 = time.time()
                issues = self.compliance_engine.check_compliance(
                    sections, metadata, contract_type
                )
                t_compliance = time.time() - _t0
            
            # Step 5.5: Check spelling errors
            spelling_errors = []
            if self.config.analyze_spelling:
                logger.info("Checking spelling errors...")
                _t0 = time.time()
                spelling_errors = self.spelling_checker.check_text(text, metadata.language)
                t_spelling = time.time() - _t0
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
                _t0 = time.time()
                
                # Enhanced analysis with RAG for risk scoring (before RAG full analysis)
                clause_analyses = None
                if self.config.use_rag and self.rag:
                    try:
                        logger.info("Running LLM-based clause analysis for risk scoring...")
                        clause_analyses = self._run_clause_analyses_for_risk(sections, contract_type)
                    except Exception as e:
                        logger.error(f"LLM clause analysis failed: {e}, falling back to traditional scoring")
                        clause_analyses = None
                
                # Pass LLM analyses to risk engine
                risk_score = self.risk_engine.calculate_score(
                    sections, metadata, issues, contract_type, clause_analyses
                )
                t_risk = time.time() - _t0
            
            # Step 7: Enhanced analysis with RAG (if available)
            enhanced_analysis = {}
            if self.config.use_rag and self.rag:
                logger.info("Running enhanced RAG analysis...")
                _t0 = time.time()
                enhanced_analysis = self._run_rag_analysis(text, sections, contract_type)
                t_rag = time.time() - _t0
            
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
                    'ambiguity_score': getattr(risk_score, 'ambiguity_score', 50) if risk_score else 50,
                    'specificity_score': getattr(risk_score, 'specificity_score', 50) if risk_score else 50,
                'summary': summary,
                'recommendations': risk_score.recommendations if risk_score else [],
                'enhanced_analysis': enhanced_analysis,
                'processing_time': processing_time,
                'metrics': {
                    't_ocr': round(t_ocr, 3),
                    't_parse': round(t_parse, 3),
                    't_spelling': round(t_spelling, 3),
                    't_compliance': round(t_compliance, 3),
                    't_risk': round(t_risk, 3),
                    't_rag': round(t_rag, 3),
                },
                'model_used': f"{self.rag.llm_type}:{self.rag.llm_model if self.rag.llm_type == 'ollama' else (self.rag.gemini_model if self.rag.llm_type == 'gemini' else self.rag.openai_model)}" if self.rag and self.rag.llm_type else "rule-based",
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
                # Uzbek (Latin) and Russian
                'pudrat', 'подряд', 'qurilish', 'qurish', "ta'mirlash",
                'строительство', 'ремонт',
                # Uzbek (Cyrillic) variants
                'пудрат', 'қурилиш', 'курилиш', 'қуриш', 'иншоот', 'иншоат'
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
            contract.currency = metadata.currency
        
        from apps.contracts.models import Contract as ContractModel

        language_defaults = {
            ContractModel.Language.UZ_LATN,
            ContractModel.Language.UZ_CYRL,
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
    
    def _run_clause_analyses_for_risk(self, sections: List[Section], contract_type: str) -> Dict[str, ClauseAnalysis]:
        """
        Run structured clause analyses using LLM for risk scoring.
        Analyzes key sections to determine compliance and risks.
        """
        clause_analyses = {}
        
        # SKIP LLM ANALYSIS TO SAVE QUOTA FOR SUMMARY
        # We only have 20 requests/day on free tier.
        # Summary is more important.
        logger.info("Skipping structured analysis to save Gemini quota for summary.")
        return clause_analyses

        # Tahlil qilish uchun asosiy bo'limlar
        key_sections = [
            SectionType.LIABILITY,      # Javobgarlik - xavfli
            SectionType.PRICE,          # Narx - cheksiz bo'lishi mumkin
            SectionType.TERM,           # Muddat - muammoli bo'lishi mumkin
            SectionType.FORCE_MAJEURE,  # Fors-major - cheklash mumkin
        ]
        
        try:
            for section in sections:
                if section.section_type in key_sections:
                    try:
                        # Rate limiting for Gemini (avoid 429 errors)
                        if self.config.use_gemini or getattr(self.rag, 'llm_type', '') == 'gemini':
                            time.sleep(15)

                        # Get structured analysis from LLM
                        structured = self.rag.analyze_clause_structured(
                            section.content[:1000],
                            contract_type
                        )
                        
                        # Extract data from structured analysis
                        analysis_data = structured.get('analysis_structured', {})
                        
                        # Determine severity based on compliance
                        compliance = analysis_data.get('compliance', 'noaniq')
                        severity = 'critical' if compliance == 'mos emas' else 'medium'
                        
                        # Create ClauseAnalysis object
                        clause_analyses[section.section_type.value] = ClauseAnalysis(
                            clause_text=section.content[:500],
                            compliance=compliance,
                            risks=analysis_data.get('risks', []),
                            recommendations=analysis_data.get('recommendations', []),
                            severity=severity,
                            suggested_text=analysis_data.get('rewrite', ''),
                        )
                        
                        logger.info(f"[LLM ANALYSIS] {section.section_type.value}: {compliance}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to analyze section {section.section_type.value}: {e}")
                        # Continue with next section if one fails
                        continue
        
        except Exception as e:
            logger.error(f"Clause analysis for risk failed: {e}")
        
        return clause_analyses
    
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
            section_analyses_structured = {}
            
            for section in sections:
                if section.section_type in key_sections:
                    analysis = self.rag.analyze_clause(
                        section.content[:1000],
                        contract_type
                    )
                    section_analyses[section.section_type.value] = analysis.get('analysis', '')
                    # Try structured analysis
                    try:
                        structured = self.rag.analyze_clause_structured(
                            section.content[:800],
                            contract_type
                        )
                        section_analyses_structured[section.section_type.value] = structured.get('analysis_structured')
                    except Exception as e:
                        section_analyses_structured[section.section_type.value] = {'error': str(e)}
            
            results['section_analyses'] = section_analyses
            results['section_analyses_structured'] = section_analyses_structured
            
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
        """Generate human-readable analysis summary (LLM-backed if available)."""
        # Prefer LLM summary when enabled and RAG/OpenAI is available
        try:
            if self.config.use_llm and self.rag is not None and getattr(self.rag, 'llm_type', None):
                # Rate limiting for Gemini
                if getattr(self.rag, 'llm_type', '') == 'gemini':
                    time.sleep(15)
                    
                llm_summary = self._generate_llm_summary(sections, metadata, issues, risk_score)
                if llm_summary and isinstance(llm_summary, str) and len(llm_summary.strip()) > 0:
                    # Append provenance note
                    llm_name = getattr(self.rag, 'llm_type', 'llm')
                    if llm_name == 'openai':
                        llm_name = f"OpenAI ({getattr(self.rag, 'openai_model', '')})".strip()
                    elif llm_name == 'ollama':
                        llm_name = f"Ollama ({getattr(self.rag, 'llm_model', '')})".strip()
                    elif llm_name == 'gemini':
                        llm_name = f"Gemini ({getattr(self.rag, 'gemini_model', '')})".strip()
                    provenance = f"\n\n(LLM xulosa manbasi: {llm_name})"
                    return llm_summary + provenance
        except Exception as e:
            logger.warning(f"LLM summary generation failed, falling back: {e}")

        # Fallback: existing rule-based summary
        summary_parts = []

        summary_parts.append("📄 SHARTNOMA TAHLILI NATIJALARI")
        summary_parts.append("=" * 50)

        if metadata.contract_number:
            summary_parts.append(f"\n📋 Shartnoma raqami: {metadata.contract_number}")
        if metadata.contract_date:
            summary_parts.append(f"📅 Sana: {metadata.contract_date}")

        summary_parts.append(f"\n🔍 Tahlil qilingan bo'limlar: {len(sections)}")

        # Highlight missing essentials
        try:
            from ai_engine.compliance import LegalComplianceEngine, get_section_name
            required_sections = LegalComplianceEngine.REQUIRED_SECTIONS.get(
                getattr(risk_score, 'contract_type', ''),
                LegalComplianceEngine.REQUIRED_SECTIONS.get("service", [])
            ) if risk_score else []
            found_types = {s.section_type for s in sections}
            missing_sections = [get_section_name(sec.value, metadata.language) for sec in required_sections if sec not in found_types]
            missing_fields = []
            if not metadata.contract_number:
                missing_fields.append("shartnoma raqami")
            if not metadata.contract_date:
                missing_fields.append("sana")
            if not metadata.total_amount:
                missing_fields.append("summasi")
            if not (metadata.party_a_name or metadata.party_a_inn):
                missing_fields.append("1-tomon ma'lumotlari")
            if not (metadata.party_b_name or metadata.party_b_inn):
                missing_fields.append("2-tomon ma'lumotlari")
            if missing_sections:
                summary_parts.append(f"🚩 Yetishmayotgan bo'limlar: {', '.join(missing_sections)}")
            if missing_fields:
                summary_parts.append(f"🚩 Yetishmayotgan muhim ma'lumotlar: {', '.join(missing_fields)}")
        except Exception:
            pass

        if risk_score:
            score = risk_score.overall_score
            if score >= 80:
                emoji = "✅"; message = "A'LO DARAJADA! Shartnoma qonun talablariga to'liq mos keladi."
            elif score >= 70:
                emoji = "✅"; message = "YAXSHI! Shartnoma asosan qonun talablariga mos."
            elif score >= 50:
                emoji = "⚠️"; message = "O'RTA DARAJA. Ayrim bandlarni yaxshilash tavsiya etiladi."
            elif score >= 30:
                emoji = "⚠️"; message = "E'TIBOR BERING! Bir nechta muhim kamchiliklar bor."
            else:
                emoji = "🔴"; message = "JIDDIY MUAMMOLAR! Shartnomani yurist bilan ko'rib chiqish tavsiya etiladi."
            summary_parts.append(f"\n{emoji} UMUMIY BAHO: {score}/100")
            summary_parts.append(f"{message}")

        if issues:
            critical_count = sum(1 for i in issues if i.severity.value == 'critical')
            high_count = sum(1 for i in issues if i.severity.value == 'high')
            medium_count = sum(1 for i in issues if i.severity.value == 'medium')
            low_count = sum(1 for i in issues if i.severity.value == 'low')

            summary_parts.append(f"\n📊 Topilgan muammolar:")
            if critical_count: summary_parts.append(f"🔴 Jiddiy: {critical_count} ta")
            if high_count: summary_parts.append(f"🟠 Yuqori: {high_count} ta")
            if medium_count: summary_parts.append(f"🟡 O'rta: {medium_count} ta")
            if low_count: summary_parts.append(f"🟢 Past: {low_count} ta")

            critical_issues = [i for i in issues if i.severity.value == 'critical']
            if critical_issues:
                summary_parts.append(f"\n⚠️ Jiddiy muammolar (qisqa):")
                for issue in critical_issues[:3]:
                    summary_parts.append(f"• {issue.title}")
        else:
            summary_parts.append(f"\n✅ Jiddiy muammolar topilmadi!")

        if risk_score and risk_score.overall_score >= 70:
            summary_parts.append("\n💡 Shartnoma yaxshi tuzilgan. Kichik takomillashtirishlar bilan ishlatish mumkin.")

        # Fallback provenance note
        summary_parts.append("\n(LLM xulosa manbasi: Fallback qoida asosidagi xulosa — LLM ishlamadi yoki o‘chirib qo‘yilgan)")

        return "\n".join(summary_parts)

    def _generate_llm_summary(
        self,
        sections: List[Section],
        metadata: ContractMetadata,
        issues: List[ComplianceIssue],
        risk_score: Optional[RiskScore]
    ) -> str:
        """Use LLM (OpenAI/Ollama via LegalRAG) to craft a concise, human-friendly Uzbek summary."""
        try:
            # Build structured context
            crit = [i for i in issues if i.severity.value == 'critical']
            high = [i for i in issues if i.severity.value == 'high']
            med = [i for i in issues if i.severity.value == 'medium']
            low = [i for i in issues if i.severity.value == 'low']

            meta_lines = []
            if metadata.contract_number: meta_lines.append(f"Shartnoma raqami: {metadata.contract_number}")
            if metadata.contract_date: meta_lines.append(f"Sana: {metadata.contract_date}")
            if metadata.party_a_name: meta_lines.append(f"1-tomon: {metadata.party_a_name}")
            if metadata.party_b_name: meta_lines.append(f"2-tomon: {metadata.party_b_name}")
            if metadata.total_amount and metadata.currency:
                meta_lines.append(f"Summa: {metadata.total_amount} {metadata.currency}")
            meta_lines.append(f"Bo'limlar soni: {len(sections)}")

            score_block = []
            if risk_score:
                score_block.append(f"Umumiy baho: {risk_score.overall_score}/100")
                score_block.append(f"Xavf darajasi: {risk_score.risk_level.value}")
                score_block.append(f"Qonunga moslik: {risk_score.compliance_score}/100")
                score_block.append(f"To'liqlik: {risk_score.completeness_score}/100")
                score_block.append(f"Aniqlik: {risk_score.clarity_score}/100")
                score_block.append(f"Muvozanat: {risk_score.balance_score}/100")

            issues_block = [
                f"Jiddiy: {len(crit)} ta",
                f"Yuqori: {len(high)} ta",
                f"O'rta: {len(med)} ta",
                f"Past: {len(low)} ta",
            ]
            short_crit = [f"- {i.title}" for i in crit[:3]]

            # Construct contract text (truncated to avoid token limits)
            # OpenAI GPT-3.5 has 16k context, Gemini has huge context.
            # We'll use a safe limit of ~12000 chars (approx 3000 tokens) to leave room for response.
            full_text = "\n\n".join([f"--- {s.title} ---\n{s.content}" for s in sections])
            truncated_text = full_text[:12000]
            if len(full_text) > 12000:
                truncated_text += "\n...(davomi kesib tashlandi)..."

            # Language warning
            lang_warning = ""
            if hasattr(metadata, 'language_distribution') and metadata.language_distribution:
                dist = metadata.language_distribution
                # Check if mixed
                main_lang = max(dist, key=dist.get)
                main_ratio = dist[main_lang]
                
                if main_ratio < 0.9: # If dominant language is less than 90%
                    lang_warning = (
                        f"\nDIQQAT: Shartnoma tili aralash bo'lishi mumkin. "
                        f"Asosiy til: {main_lang} ({main_ratio:.0%}). "
                        f"Boshqa tillar: {', '.join([f'{k} ({v:.0%})' for k,v in dist.items() if k != main_lang and v > 0.05])}. "
                        "Shartnomani yagona tilda rasmiylashtirish tavsiya etiladi."
                    )

            prompt = (
                "Quyidagi shartnoma matnini O'zbekiston qonunchiligi va manfaatlar muvozanati nuqtai nazaridan chuqur tahlil qiling.\n"
                "Statistikaga emas, matnning mazmuniga e'tibor bering.\n\n"
                f"[SHARTNOMA MATNI (Qisqartirilgan)]\n{truncated_text}\n\n"
                "[TAHLIL MA'LUMOTLARI]\n" + "\n".join(meta_lines) + "\n" +
                f"Topilgan texnik muammolar soni: {len(issues)}\n"
                f"{lang_warning}\n\n"
                "TALABLAR:\n"
                "1. Shartnoma mohiyati: 1 gapda nima haqida ekanligini yozing.\n"
                "2. XAVFLAR: Matn ichidan mijoz uchun eng xavfli, noaniq yoki bir tomonlama 2-3 ta aniq bandni toping va ularning oqibatini tushuntiring.\n"
                "3. YECHIM: Ushbu xavflarni bartaraf etish uchun aniq yuridik maslahat bering.\n"
                "4. TIL VA USLUB: Agar shartnoma tili aralash bo'lsa, buni alohida ta'kidlang va yagona tilga o'tkazishni maslahat bering. Qattiqqo'l auditor kabi yozing.\n"
            )

            # Use LLM without retrieval context (we just need wording)
            system_prompt = (
                "Siz tajribali yurist va auditorsiz. Sizning vazifangiz shartnomadagi yashirin xavflarni, "
                "mijoz zarariga ishlaydigan bandlarni va yetishmayotgan himoya mexanizmlarini aniqlash. "
                "Javobingiz lo'nda, tanqidiy va amaliy bo'lishi shart."
            )

            if getattr(self.rag, 'llm_type', None) == 'ollama':
                resp = self.rag.llm_client.chat(
                    model=self.rag.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    options={"temperature": 0.2, "num_predict": 512},
                )
                return resp['message']['content']
            elif getattr(self.rag, 'llm_type', None) == 'openai':
                resp = self.rag.openai_client.chat.completions.create(
                    model=self.rag.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=512,
                )
                return resp.choices[0].message.content
            elif getattr(self.rag, 'llm_type', None) == 'gemini':
                import google.generativeai as genai
                from google.generativeai.types import HarmCategory, HarmBlockThreshold
                try:
                    # No sleep needed if we skipped structured analysis
                    # time.sleep(15) 
                    
                    # Create model with system instruction
                    model = genai.GenerativeModel(
                        self.rag.gemini_model,
                        system_instruction=system_prompt
                    )
                    
                    resp = model.generate_content(
                        prompt,
                        generation_config=dict(
                            temperature=0.2,
                            max_output_tokens=2048,
                        ),
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    if resp.parts:
                        return resp.text
                    else:
                        logger.warning(f"Gemini blocked response. Feedback: {resp.prompt_feedback}")
                        if resp.candidates and resp.candidates[0].content.parts:
                             return resp.candidates[0].content.parts[0].text
                        return "Xulosa yaratishda xatolik: AI xavfsizlik filtri tomonidan bloklandi."
                except Exception as e:
                    logger.error(f"Gemini generation error: {e}")
                    return ""
            return ""
        except Exception as e:
            logger.warning(f"LLM summary error: {e}")
            return ""
    
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
