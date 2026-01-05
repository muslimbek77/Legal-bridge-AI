#!/usr/bin/env python3
"""
Test real contract analysis from shartnomalar folder.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/rasulbek/muslim-projects/Legal-bridge-AI/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files import File
from apps.contracts.models import Contract
from apps.analysis.models import AnalysisResult, ComplianceIssue
from ai_engine.pipeline import ContractAnalysisPipeline, AnalysisConfig


def test_real_contract(file_path: str):
    """Test analysis on a real contract file."""
    
    print("\n" + "="*80)
    print(f"HAQIQIY SHARTNOMA TAHLILI")
    print(f"Fayl: {os.path.basename(file_path)}")
    print("="*80)
    
    # Create contract in database
    with open(file_path, 'rb') as f:
        contract = Contract.objects.create(
            title=os.path.basename(file_path),
            contract_type='other',
            description='Test shartnoma',
            original_file=File(f, name=os.path.basename(file_path))
        )
    
    print(f"✓ Shartnoma yaratildi: {contract.id}")
    
    # Run analysis
    config = AnalysisConfig(
        analyze_compliance=True,
        analyze_risks=True,
        analyze_spelling=False,  # Skip spelling check
        use_rag=False,  # Skip RAG for quick test
    )
    
    pipeline = ContractAnalysisPipeline(config)
    
    try:
        result = pipeline.analyze(contract)
        
        print(f"\n{'='*80}")
        print("TAHLIL NATIJALARI")
        print('='*80)
        
        print(f"\n📄 Shartnoma turi: {result.get('contract_type', 'noma\'lum')}")
        print(f"📊 Umumiy ball: {result.get('overall_score', 0)}/100")
        print(f"⚠️  Xavf darajasi: {result.get('risk_level', 'noma\'lum').upper()}")
        
        print(f"\n📈 Tarkibiy ballar:")
        print(f"   • Qonunga moslik: {result.get('compliance_score', 0)}/100")
        print(f"   • To'liqlik: {result.get('completeness_score', 0)}/100")
        print(f"   • Aniqlik: {result.get('clarity_score', 0)}/100")
        print(f"   • Muvozanat: {result.get('balance_score', 0)}/100")
        
        issues = result.get('issues', [])
        print(f"\n📋 Topilgan muammolar: {len(issues)}")
        
        # Group by severity
        by_severity = {}
        for issue in issues:
            sev = issue.get('severity', 'unknown')
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        if by_severity:
            print(f"\n   Darajalar bo'yicha:")
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢',
                'info': 'ℹ️'
            }
            for sev in ['critical', 'high', 'medium', 'low', 'info']:
                if sev in by_severity:
                    emoji = severity_emoji.get(sev, '•')
                    print(f"   {emoji} {sev.upper()}: {by_severity[sev]}")
        
        # Show critical and high issues
        critical_issues = [i for i in issues if i.get('severity') in ['critical', 'high']]
        if critical_issues:
            print(f"\n⚠️  JIDDIY MUAMMOLAR ({len(critical_issues)}):")
            for i, issue in enumerate(critical_issues[:10], 1):
                print(f"\n   {i}. [{issue.get('severity', '').upper()}] {issue.get('title', '')}")
                desc = issue.get('description', '')
                if len(desc) > 150:
                    desc = desc[:150] + '...'
                print(f"      → {desc}")
                if issue.get('suggestion'):
                    sug = issue.get('suggestion', '')
                    if len(sug) > 100:
                        sug = sug[:100] + '...'
                    print(f"      💡 {sug}")
        
        # Show summary
        summary = result.get('summary', '')
        if summary:
            print(f"\n{'='*80}")
            print("XULOSA:")
            print('='*80)
            print(summary)
        
        # Show recommendations
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"\n{'='*80}")
            print("TAVSIYALAR:")
            print('='*80)
            for i, rec in enumerate(recommendations[:7], 1):
                print(f"{i}. {rec}")
        
        # Cleanup
        contract.delete()
        print(f"\n✓ Test shartnoma o'chirildi")
        
        return result
        
    except Exception as e:
        print(f"\n❌ XATOLIK: {e}")
        import traceback
        traceback.print_exc()
        contract.delete()
        return None


if __name__ == "__main__":
    # Test with uzbek contract
    contract_file = '/home/rasulbek/muslim-projects/Legal-bridge-AI/shartnomalar/самарканд услуга.docx'
    
    if os.path.exists(contract_file):
        test_real_contract(contract_file)
    else:
        print(f"❌ Fayl topilmadi: {contract_file}")
