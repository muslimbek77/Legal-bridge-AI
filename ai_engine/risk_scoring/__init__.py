"""
Risk Scoring Module.
Calculates risk scores for contracts based on compliance issues and analysis.
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
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
        contract_type: str = "other"
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for a contract.
        
        Args:
            sections: Parsed contract sections
            metadata: Contract metadata
            issues: Compliance issues found
            contract_type: Type of contract
            
        Returns:
            RiskScore object with detailed assessment
        """
        # Calculate individual scores
        compliance_score = self._calculate_compliance_score(issues)
        completeness_score = self._calculate_completeness_score(sections, contract_type)
        clarity_score = self._calculate_clarity_score(sections, metadata)
        balance_score = self._calculate_balance_score(issues)
        
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
        recommendations = self._generate_recommendations(issues, overall_score)
        
        # Create breakdown
        breakdown = self._create_breakdown(issues)
        
        return RiskScore(
            overall_score=overall_score,
            risk_level=risk_level,
            compliance_score=compliance_score,
            completeness_score=completeness_score,
            clarity_score=clarity_score,
            balance_score=balance_score,
            breakdown=breakdown,
            recommendations=recommendations,
        )
    
    def _calculate_compliance_score(self, issues: List[ComplianceIssue]) -> int:
        """Calculate compliance score based on issues."""
        score = 100
        
        for issue in issues:
            # Get base deduction
            deduction = self.SEVERITY_DEDUCTIONS.get(issue.severity, 5)
            
            # Apply issue type weight
            weight = self.ISSUE_TYPE_WEIGHTS.get(issue.issue_type, 1.0)
            
            # Calculate final deduction
            final_deduction = int(deduction * weight)
            
            score -= final_deduction
        
        return max(0, min(100, score))
    
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
    
    def _calculate_balance_score(self, issues: List[ComplianceIssue]) -> int:
        """Calculate balance score based on one-sided clauses."""
        score = 100
        
        one_sided_count = sum(
            1 for issue in issues 
            if issue.issue_type == IssueType.ONE_SIDED
        )
        
        # Each one-sided clause reduces balance score
        score -= one_sided_count * 15
        
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
        """Determine risk level from score."""
        if score >= 70:
            return RiskLevel.LOW
        elif score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def _generate_recommendations(self, issues: List[ComplianceIssue], score: int) -> List[str]:
        """Generate recommendations based on issues and score."""
        recommendations = []
        
        # Sort issues by severity
        sorted_issues = sorted(
            issues,
            key=lambda x: list(IssueSeverity).index(x.severity)
        )
        
        # Add recommendations for top issues
        seen_titles = set()
        for issue in sorted_issues[:5]:
            if issue.suggestion and issue.title not in seen_titles:
                recommendations.append(issue.suggestion)
                seen_titles.add(issue.title)
        
        # Add general recommendations based on score
        if score < 30:
            recommendations.append(
                "Shartnomani tubdan qayta ko'rib chiqish tavsiya etiladi"
            )
        elif score < 50:
            recommendations.append(
                "Shartnomada bir nechta muhim kamchiliklar mavjud"
            )
        elif score < 70:
            recommendations.append(
                "Shartnoma yaxshi, lekin ayrim o'zgartirishlar kiritish kerak"
            )
        else:
            recommendations.append(
                "Shartnoma asosan qonun talablariga mos keladi"
            )
        
        return recommendations[:7]  # Limit to 7 recommendations
    
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
