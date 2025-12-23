"""
Risk Scoring Module.
Calculates risk scores for contracts based on compliance issues and analysis.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from ai_engine.compliance import ComplianceIssue, IssueSeverity, IssueType
from ai_engine.parser import Section, SectionType, ContractMetadata

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level categories."""
    HIGH = "high"       # 0-30
    MEDIUM = "medium"   # 30-70
    LOW = "low"         # 70-100


@dataclass
class RiskScore:
    """Complete risk assessment for a contract."""
    overall_score: int  # 0-100
    risk_level: RiskLevel
    compliance_score: int
    completeness_score: int
    clarity_score: int
    balance_score: int
    breakdown: Dict[str, int]
    recommendations: List[str]
    risky_clauses: List[Dict] = field(default_factory=list)  # Xavfli bandlar
    enhanced_by_llm: bool = False  # LLM orqali yaxşilangan


@dataclass
class ClauseAnalysis:
    """Represents analysis result for a single clause."""
    clause_text: str
    compliance: str  # "mos", "mos emas", "noaniq"
    risks: List[str]  # Aniqlangan xavflar
    recommendations: List[str]  # Tavsiyalar
    severity: str  # "critical", "high", "medium", "low"
    suggested_text: str = ""  # Taklif etilgan tekst


class RiskScoringEngine:
    """
    Engine for calculating contract risk scores.
    
    Scoring methodology:
    - Overall score: 0-100 (higher is better)
    - Based on: compliance, completeness, clarity, balance
    - Issues reduce score based on severity
    """
    
    # Severity score deductions
    SEVERITY_DEDUCTIONS = {
        IssueSeverity.CRITICAL: 15,
        IssueSeverity.HIGH: 10,
        IssueSeverity.MEDIUM: 5,
        IssueSeverity.LOW: 2,
        IssueSeverity.INFO: 0,
    }
    
    # Issue type specific deductions
    ISSUE_TYPE_WEIGHTS = {
        IssueType.ILLEGAL: 1.5,
        IssueType.MISSING_CLAUSE: 1.2,
        IssueType.INVALID_CLAUSE: 1.3,
        IssueType.ONE_SIDED: 1.1,
        IssueType.MISSING_INFO: 1.0,
        IssueType.UNCLEAR: 0.8,
        IssueType.FORMAT: 0.7,
        IssueType.CONFLICT: 1.2,
        IssueType.SPELLING: 0.3,  # Imloviy xatolar uchun kichik chegirma
        IssueType.GRAMMAR: 0.4,   # Grammatik xatolar uchun kichik chegirma
        IssueType.OTHER: 0.5,
    }
    
    # Section weights for completeness
    SECTION_WEIGHTS = {
        SectionType.PARTIES: 10,
        SectionType.SUBJECT: 10,
        SectionType.PRICE: 10,
        SectionType.TERM: 8,
        SectionType.OBLIGATIONS: 8,
        SectionType.LIABILITY: 8,
        SectionType.REQUISITES: 8,
        SectionType.WARRANTY: 6,
        SectionType.DELIVERY: 6,
        SectionType.QUALITY: 6,
        SectionType.FORCE_MAJEURE: 4,
        SectionType.DISPUTE: 4,
        SectionType.RIGHTS: 4,
        SectionType.TERMINATION: 3,
        SectionType.CONFIDENTIAL: 2,
        SectionType.ADDITIONAL: 2,
    }
    
    def __init__(self):
        """Initialize the risk scoring engine."""
        pass
    
    def calculate_score(
        self,
        sections: List[Section],
        metadata: ContractMetadata,
        issues: List[ComplianceIssue],
        contract_type: str = "other",
        clause_analyses: Optional[Dict[str, ClauseAnalysis]] = None  # LLM natijalari
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for a contract.
        
        Args:
            sections: Parsed contract sections
            metadata: Contract metadata
            issues: Compliance issues found
            contract_type: Type of contract
            clause_analyses: Optional dict of ClauseAnalysis from LLM
            
        Returns:
            RiskScore object with detailed assessment
        """
        # Calculate individual scores
        compliance_score = self._calculate_compliance_score(issues, clause_analyses)
        completeness_score = self._calculate_completeness_score(sections, contract_type)
        clarity_score = self._calculate_clarity_score(sections, metadata)
        balance_score = self._calculate_balance_score(issues, clause_analyses)
        
        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score(
            compliance_score,
            completeness_score,
            clarity_score,
            balance_score
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, overall_score, clause_analyses)
        
        # Create breakdown
        breakdown = self._create_breakdown(issues)
        
        # Extract risky clauses from LLM analysis
        risky_clauses = self._extract_risky_clauses(clause_analyses) if clause_analyses else []
        
        return RiskScore(
            overall_score=overall_score,
            risk_level=risk_level,
            compliance_score=compliance_score,
            completeness_score=completeness_score,
            clarity_score=clarity_score,
            balance_score=balance_score,
            breakdown=breakdown,
            recommendations=recommendations,
            risky_clauses=risky_clauses,
            enhanced_by_llm=bool(clause_analyses),
        )
    
    def _calculate_compliance_score(
        self, 
        issues: List[ComplianceIssue],
        clause_analyses: Optional[Dict[str, ClauseAnalysis]] = None
    ) -> int:
        """Calculate compliance score based on issues and LLM analysis."""
        score = 100
        total_deduction = 0
        
        # Traditional method: issues'dan chegirma
        for issue in issues:
            # Get base deduction (yumshatilgan)
            deduction = self.SEVERITY_DEDUCTIONS.get(issue.severity, 3)
            # Apply issue type weight (yumshatilgan)
            weight = min(self.ISSUE_TYPE_WEIGHTS.get(issue.issue_type, 1.0), 1.0)
            # Calculate final deduction
            final_deduction = int(deduction * weight)
            total_deduction += final_deduction
        
        # LLM natijalari: mos emas bandlar uchun katta chegirma
        if clause_analyses:
            critical_risks = 0
            non_compliant_count = 0
            
            for analysis in clause_analyses.values():
                # Count compliance issues
                if analysis.compliance == "mos emas":
                    non_compliant_count += 1
                
                # Count critical/high severity issues
                if analysis.severity in ["critical", "high"]:
                    critical_risks += 1
            
            # Har bir "mos emas" ban uchun 20 ball chegirma (yuqori!)
            total_deduction += non_compliant_count * 20
            
            # Critical/high severity uchun xosil chegirma
            total_deduction += critical_risks * 12
        
        # Har bir muammo uchun maksimal chegirma 80% dan oshmasin (20 ball qolsin)
        max_total_deduction = 80
        score -= min(total_deduction, max_total_deduction)
        
        # Minimal muvofiqlik darajasi 10% dan past tushmaydi
        return max(10, min(100, score))
    
    def _calculate_completeness_score(self, sections: List[Section], contract_type: str) -> int:
        """Calculate completeness score based on sections present."""
        # Get required sections for contract type
        from ai_engine.compliance import LegalComplianceEngine
        required_sections = LegalComplianceEngine.REQUIRED_SECTIONS.get(
            contract_type,
            LegalComplianceEngine.REQUIRED_SECTIONS.get("service", [])
        )
        
        if not required_sections:
            return 100
        
        found_types = {s.section_type for s in sections}
        
        # Calculate weighted score
        total_weight = sum(self.SECTION_WEIGHTS.get(s, 5) for s in required_sections)
        found_weight = sum(
            self.SECTION_WEIGHTS.get(s, 5) 
            for s in required_sections 
            if s in found_types
        )
        
        if total_weight == 0:
            return 100
        
        score = int((found_weight / total_weight) * 100)
        return max(0, min(100, score))
    
    def _calculate_clarity_score(self, sections: List[Section], metadata: ContractMetadata) -> int:
        """Calculate clarity score based on text quality."""
        score = 100
        
        # Check metadata completeness
        if not metadata.contract_number:
            score -= 5
        if not metadata.contract_date:
            score -= 10
        if not metadata.party_a_name and not metadata.party_a_inn:
            score -= 10
        if not metadata.party_b_name and not metadata.party_b_inn:
            score -= 10
        
        # Check section content quality
        for section in sections:
            # Penalize very short sections
            if len(section.content) < 50:
                score -= 3
            
            # Penalize unclear language patterns
            unclear_patterns = [
                "va hokazo",
                "va boshqalar",
                "и т.д.",
                "и прочее",
                "taxminan",
                "примерно",
                "taxminan",
            ]
            content_lower = section.content.lower()
            for pattern in unclear_patterns:
                if pattern in content_lower:
                    score -= 2
        
        return max(0, min(100, score))
    
    def _calculate_balance_score(
        self, 
        issues: List[ComplianceIssue],
        clause_analyses: Optional[Dict[str, ClauseAnalysis]] = None
    ) -> int:
        """Calculate balance score based on one-sided clauses and LLM risks."""
        score = 100
        
        # Traditional method: ONE_SIDED issues
        one_sided_count = sum(
            1 for issue in issues 
            if issue.issue_type == IssueType.ONE_SIDED
        )
        score -= one_sided_count * 15
        
        # LLM natijalari: "bir tomonli", "asymmetric", "unfair" xavflar uchun chegirma
        if clause_analyses:
            for analysis in clause_analyses.values():
                risk_text = ' '.join(analysis.risks).lower()
                
                # Xavfli kalitlar
                one_sided_keywords = [
                    'bir tomonli', 'bir tomoni', 'asymmetric', 'nomnusbat',
                    'nobarobar', 'tengsizlik', 'notengi', 'unfair'
                ]
                
                if any(keyword in risk_text for keyword in one_sided_keywords):
                    score -= 12
        
        return max(0, min(100, score))
    
    def _calculate_overall_score(
        self,
        compliance_score: int,
        completeness_score: int,
        clarity_score: int,
        balance_score: int
    ) -> int:
        """Calculate weighted overall score."""
        # Weights for each component
        weights = {
            'compliance': 0.40,
            'completeness': 0.25,
            'clarity': 0.20,
            'balance': 0.15,
        }
        
        overall = (
            compliance_score * weights['compliance'] +
            completeness_score * weights['completeness'] +
            clarity_score * weights['clarity'] +
            balance_score * weights['balance']
        )
        
        return int(overall)
    
    def _determine_risk_level(self, score: int) -> RiskLevel:
        """Determine risk level from score. Adjusted for LLM critical findings."""
        if score >= 70:
            return RiskLevel.LOW
        elif score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def _generate_recommendations(
        self, 
        issues: List[ComplianceIssue], 
        score: int,
        clause_analyses: Optional[Dict[str, ClauseAnalysis]] = None
    ) -> List[str]:
        """Generate human-friendly recommendations based on issues, score, and LLM analysis."""
        recommendations = []
        
        # General assessment first
        if score >= 80:
            recommendations.append("✅ Shartnomangiz a'lo darajada! Barcha asosiy talablar bajarilgan.")
        elif score >= 70:
            recommendations.append("👍 Shartnomangiz yaxshi holatda. Kichik takomillashtirishlar bilan juda yaxshi bo'ladi.")
        elif score >= 50:
            recommendations.append("⚠️ Shartnomada ayrim kamchiliklar bor. Quyidagi tavsiyalarga amal qiling:")
        elif score >= 30:
            recommendations.append("⚠️ Shartnomani yaxshilash kerak. Muhim kamchiliklar mavjud:")
        else:
            recommendations.append("🔴 Shartnomani yurist bilan ko'rib chiqish juda tavsiya etiladi:")
        
        # Add specific recommendations from issues (only critical/high)
        critical_issues = sorted(
            [i for i in issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]],
            key=lambda x: list(IssueSeverity).index(x.severity)
        )
        
        seen_suggestions = set()
        for issue in critical_issues[:5]:
            if issue.suggestion and issue.suggestion not in seen_suggestions:
                # Make suggestion more friendly
                friendly_suggestion = issue.suggestion
                if not friendly_suggestion.startswith(('✓', '•', '-', '→', '💡')):
                    friendly_suggestion = f"• {friendly_suggestion}"
                recommendations.append(friendly_suggestion)
                seen_suggestions.add(issue.suggestion)
        
        # Add recommendations from LLM analysis (only for critical sections)
        if clause_analyses:
            critical_llm = [
                (name, analysis) for name, analysis in clause_analyses.items()
                if analysis.severity in ["critical", "high"] and analysis.recommendations
            ]
            
            for section_name, analysis in critical_llm[:2]:
                if analysis.recommendations:
                    rec = analysis.recommendations[0]
                    if rec not in [r.split(': ', 1)[-1] if ': ' in r else r for r in recommendations]:
                        recommendations.append(f"• {section_name}: {rec}")
        
        # Final encouraging note
        if score >= 60:
            recommendations.append("💡 Yuqoridagi takomillashtirishlarni amalga oshirganingizdan so'ng, shartnoma to'liq yaroqli bo'ladi.")
        
        return recommendations[:8]  # Maksimal 8 tavsiya
    
    def _extract_risky_clauses(self, clause_analyses: Dict[str, ClauseAnalysis]) -> List[Dict]:
        """Extract and format risky clauses from LLM analysis."""
        risky_clauses = []
        
        for section_name, analysis in clause_analyses.items():
            if analysis.compliance != "mos" or analysis.risks:
                risky_clauses.append({
                    'section': section_name,
                    'compliance': analysis.compliance,
                    'risks': analysis.risks[:3],  # Top 3 xavflar
                    'recommendations': analysis.recommendations[:2],  # Top 2 tavsiya
                    'severity': analysis.severity,
                    'suggested_text': analysis.suggested_text,
                })
        
        # Risk darajasiga qarab sorting
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        risky_clauses.sort(
            key=lambda x: severity_order.get(x['severity'], 4)
        )
        
        return risky_clauses
    
    def _create_breakdown(self, issues: List[ComplianceIssue]) -> Dict[str, int]:
        """Create issue breakdown by type and severity."""
        breakdown = {
            'by_severity': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0,
            },
            'by_type': {
                'missing_clause': 0,
                'invalid_clause': 0,
                'one_sided': 0,
                'missing_info': 0,
                'illegal': 0,
                'other': 0,
            },
            'total_issues': len(issues),
        }
        
        for issue in issues:
            severity_key = issue.severity.value
            if severity_key in breakdown['by_severity']:
                breakdown['by_severity'][severity_key] += 1
            
            type_key = issue.issue_type.value
            if type_key in breakdown['by_type']:
                breakdown['by_type'][type_key] += 1
            else:
                breakdown['by_type']['other'] += 1
        
        return breakdown
    
    def get_risk_summary(self, risk_score: RiskScore) -> str:
        """Generate a human-readable risk summary."""
        level_descriptions = {
            RiskLevel.HIGH: "YUQORI XAVF",
            RiskLevel.MEDIUM: "O'RTA XAVF",
            RiskLevel.LOW: "PAST XAVF",
        }
        
        summary = f"""
SHARTNOMA XAVF BAHOSI
=====================
Umumiy ball: {risk_score.overall_score}/100
Xavf darajasi: {level_descriptions[risk_score.risk_level]}

Tarkibiy ballar:
- Qonunga moslik: {risk_score.compliance_score}/100
- To'liqlik: {risk_score.completeness_score}/100
- Aniqlik: {risk_score.clarity_score}/100
- Muvozanat: {risk_score.balance_score}/100

Jami muammolar: {risk_score.breakdown['total_issues']}
- Jiddiy: {risk_score.breakdown['by_severity']['critical']}
- Yuqori: {risk_score.breakdown['by_severity']['high']}
- O'rta: {risk_score.breakdown['by_severity']['medium']}
- Past: {risk_score.breakdown['by_severity']['low']}

TAVSIYALAR:
"""
        for i, rec in enumerate(risk_score.recommendations, 1):
            summary += f"{i}. {rec}\n"
        
        return summary
