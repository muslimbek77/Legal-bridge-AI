#!/usr/bin/env python3
"""
Test script for improved risk scoring with risky clauses detection.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_engine.parser import ContractParser, Section, ContractMetadata, SectionType, Clause
from ai_engine.compliance import LegalComplianceEngine, IssueSeverity, IssueType, ComplianceIssue
from ai_engine.risk_scoring import RiskScoringEngine, ClauseAnalysis


def test_risky_clause_detection():
    """Test detection of risky clauses like recursive conditions."""
    
    print("\n" + "="*80)
    print("TEST: RISKY CLAUSE DETECTION")
    print("="*80)
    
    # Create test contract with risky clauses
    test_content = """
    JAVOBGARLIK BO'LIMI:
    1. Agar bir tomon shartnoma shartlarini bajarmasа va agar shu shartnomaning 
    5-bandida aytilgan talablarni bajarmasа, u istalgan zarar uchun to'liq javobgarlik 
    ko'taradi. Bu javobgarlikdan ozod qilish mumkin emas.
    
    2. Faqat sotuvchi huquqi: tovarlarning sifatini faqat sotuvchi tekshiradi va 
    faqat sotuvchi qaror qabul qiladi.
    
    NOMA'LUM MUDDAT:
    Shartnoma har qanday muddatga tuzilishi mumkin va har qanday vaqtda bekor qilinishi mumkin.
    """
    
    # Parse test contract
    parser = ContractParser()
    sections = [
        Section(
            number=1,
            title="Javobgarlik",
            content=test_content,
            section_type=SectionType.LIABILITY,
            clauses=[],
            start_pos=0,
            end_pos=len(test_content)
        )
    ]
    
    metadata = ContractMetadata(
        contract_number="TEST-001",
        contract_date="2024-01-01",
        language="uz",
    )
    
    # Check compliance with risky clause detection
    compliance_engine = LegalComplianceEngine()
    issues = compliance_engine.detect_risky_clauses(sections, "supply")
    
    print(f"\nTopilgan xavfli bandlar soni: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"\n  {i}. {issue.title}")
        print(f"     Severity: {issue.severity.value}")
        print(f"     Description: {issue.description}")
        if issue.suggestion:
            print(f"     Suggestion: {issue.suggestion}")


def test_risk_scoring_with_llm_data():
    """Test risk scoring enhancement with LLM analysis data."""
    
    print("\n" + "="*80)
    print("TEST: RISK SCORING WITH LLM DATA")
    print("="*80)
    
    # Create test sections
    sections = [
        Section(
            number=1,
            title="Tomonlar",
            content="TOMONLAR: Sotuvchi: ABC Kompaniyasi, Xaridor: XYZ Shirkati",
            section_type=SectionType.PARTIES,
            clauses=[],
            start_pos=0,
            end_pos=50
        ),
        Section(
            number=2,
            title="Narx",
            content="NARX: 1 million so'm",
            section_type=SectionType.PRICE,
            clauses=[],
            start_pos=50,
            end_pos=100
        ),
        Section(
            number=3,
            title="Javobgarlik",
            content="Javobgarlik: Cheksiz javobgarlik bo'lgan shart",
            section_type=SectionType.LIABILITY,
            clauses=[],
            start_pos=100,
            end_pos=150
        ),
    ]
    
    metadata = ContractMetadata(
        contract_number="TEST-002",
        contract_date="2024-01-01",
        party_a_name="ABC Kompaniyasi",
        party_b_name="XYZ Shirkati",
        total_amount=1000000,
        currency="UZS",
        language="uz",
    )
    
    # Create some basic issues (add more CRITICAL ones)
    basic_issues = [
        ComplianceIssue(
            issue_type=IssueType.MISSING_INFO,
            severity=IssueSeverity.CRITICAL,
            title="INN topilmadi",
            description="Tomonlarning INN raqamlari ko'rsatilmadi",
            suggestion="INN raqamlarini qo'shing"
        ),
        ComplianceIssue(
            issue_type=IssueType.INVALID_CLAUSE,
            severity=IssueSeverity.CRITICAL,
            title="Qonunga zid shart",
            description="Shartnomada qonunga zid bandlar bor",
            suggestion="Qonunga zid bandlarni olib tashlang"
        ),
    ]
    
    # Create LLM clause analyses with MORE CRITICAL ISSUES
    clause_analyses = {
        SectionType.LIABILITY.value: ClauseAnalysis(
            clause_text="Cheksiz javobgarlik",
            compliance="mos emas",
            risks=[
                "Cheksiz javobgarlik qonunga zid", 
                "Bir tomonli shart",
                "Rekurziv shart topildi"
            ],
            recommendations=["Javobgarlikni cheklovchi shart qo'shing"],
            severity="critical",
            suggested_text="Javobgarlik asosiy qarzdan ko'p bo'lmasligi kerak"
        ),
        SectionType.PRICE.value: ClauseAnalysis(
            clause_text="1 million so'm, cheksiz miqdor",
            compliance="mos emas",
            risks=["Narx shartlari aniq emas", "Bir tomonli narx belgilash"],
            recommendations=["Aniq narx va to'lov shartlarini kiriting"],
            severity="critical",  # Changed to critical!
            suggested_text="Narx va to'lov muddatlari aniq ko'rsatilsin"
        ),
        SectionType.TERM.value: ClauseAnalysis(
            clause_text="Noma'lum muddat",
            compliance="mos emas",
            risks=["Shartnoma muddati ko'rsatilmagan", "Bir tomonli bekor qilish"],
            recommendations=["Aniq muddat belgilang"],
            severity="critical",
            suggested_text="Shartnoma aniq muddatga tuzilishi kerak"
        ),
    }
    
    # Calculate risk score with LLM data
    risk_engine = RiskScoringEngine()
    risk_score = risk_engine.calculate_score(
        sections, 
        metadata, 
        basic_issues, 
        "supply",
        clause_analyses
    )
    
    print(f"\nRisk Scoring Results:")
    print(f"  Overall Score: {risk_score.overall_score}/100")
    print(f"  Risk Level: {risk_score.risk_level.value}")
    print(f"  Compliance Score: {risk_score.compliance_score}/100")
    print(f"  Completeness Score: {risk_score.completeness_score}/100")
    print(f"  Clarity Score: {risk_score.clarity_score}/100")
    print(f"  Balance Score: {risk_score.balance_score}/100")
    print(f"  Enhanced by LLM: {risk_score.enhanced_by_llm}")
    
    if risk_score.risky_clauses:
        print(f"\n  Xavfli bandlar ({len(risk_score.risky_clauses)}):")
        for clause in risk_score.risky_clauses[:3]:
            print(f"    - {clause['section']}: {clause['compliance']} ({clause['severity']})")
    
    print(f"\n  Tavsiyalar ({len(risk_score.recommendations)}):")
    for i, rec in enumerate(risk_score.recommendations[:5], 1):
        print(f"    {i}. {rec[:80]}...")


def test_without_llm():
    """Test traditional risk scoring without LLM."""
    
    print("\n" + "="*80)
    print("TEST: TRADITIONAL RISK SCORING (WITHOUT LLM)")
    print("="*80)
    
    sections = [
        Section(
            number=1,
            title="Parties",
            content="PARTIES: Seller, Buyer",
            section_type=SectionType.PARTIES,
            clauses=[],
            start_pos=0,
            end_pos=30
        ),
    ]
    
    metadata = ContractMetadata(
        contract_number="TEST-003",
        contract_date="2024-01-01",
        language="uz",
    )
    
    # Without LLM data
    risk_engine = RiskScoringEngine()
    risk_score = risk_engine.calculate_score(
        sections,
        metadata,
        [],
        "supply"
    )
    
    print(f"\nTraditional Risk Score: {risk_score.overall_score}/100")
    print(f"Risk Level: {risk_score.risk_level.value}")
    print(f"Enhanced by LLM: {risk_score.enhanced_by_llm}")


if __name__ == "__main__":
    try:
        test_risky_clause_detection()
        test_risk_scoring_with_llm_data()
        test_without_llm()
        
        print("\n" + "="*80)
        print("✅ BARCHA TESTLAR MUVAFFAQIYATLI BAJARILDI!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST XATOSI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
