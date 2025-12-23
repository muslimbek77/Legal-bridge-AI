#!/usr/bin/env python3
"""
Django management command to test real contracts.
Place in: backend/apps/analysis/management/commands/
"""

from django.core.management.base import BaseCommand
from django.core.files import File
from apps.contracts.models import Contract
from ai_engine.pipeline import ContractAnalysisPipeline, AnalysisConfig
import os


class Command(BaseCommand):
    help = 'Test real contract analysis'

    def add_arguments(self, parser):
        parser.add_argument('contract_file', type=str, help='Path to contract file')

    def handle(self, *args, **options):
        file_path = options['contract_file']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        self.stdout.write("="*80)
        self.stdout.write(f"HAQIQIY SHARTNOMA TAHLILI")
        self.stdout.write(f"Fayl: {os.path.basename(file_path)}")
        self.stdout.write("="*80)
        
        # Create contract
        with open(file_path, 'rb') as f:
            contract = Contract.objects.create(
                title=os.path.basename(file_path),
                contract_type='other',
                description='Test shartnoma',
                original_file=File(f, name=os.path.basename(file_path))
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Shartnoma yaratildi: {contract.id}'))
        
        # Run analysis
        config = AnalysisConfig(
            analyze_compliance=True,
            analyze_risks=True,
            analyze_spelling=False,
            use_rag=False,
        )
        
        pipeline = ContractAnalysisPipeline(config)
        
        try:
            result = pipeline.analyze(contract)
            
            self.stdout.write("\n" + "="*80)
            self.stdout.write("TAHLIL NATIJALARI")
            self.stdout.write("="*80)
            
            self.stdout.write(f"\n📄 Shartnoma turi: {result.get('contract_type', 'noma\'lum')}")
            self.stdout.write(f"📊 Umumiy ball: {result.get('overall_score', 0)}/100")
            self.stdout.write(f"⚠️  Xavf darajasi: {result.get('risk_level', 'noma\'lum').upper()}")
            
            self.stdout.write(f"\n📈 Tarkibiy ballar:")
            self.stdout.write(f"   • Qonunga moslik: {result.get('compliance_score', 0)}/100")
            self.stdout.write(f"   • To'liqlik: {result.get('completeness_score', 0)}/100")
            self.stdout.write(f"   • Aniqlik: {result.get('clarity_score', 0)}/100")
            self.stdout.write(f"   • Muvozanat: {result.get('balance_score', 0)}/100")
            
            issues = result.get('issues', [])
            self.stdout.write(f"\n📋 Topilgan muammolar: {len(issues)}")
            
            # Group by severity
            by_severity = {}
            for issue in issues:
                sev = issue.get('severity', 'unknown')
                by_severity[sev] = by_severity.get(sev, 0) + 1
            
            if by_severity:
                self.stdout.write(f"\n   Darajalar bo'yicha:")
                for sev in ['critical', 'high', 'medium', 'low', 'info']:
                    if sev in by_severity:
                        self.stdout.write(f"   • {sev.upper()}: {by_severity[sev]}")
            
            # Show critical and high issues
            critical_issues = [i for i in issues if i.get('severity') in ['critical', 'high']]
            if critical_issues:
                self.stdout.write(f"\n⚠️  JIDDIY MUAMMOLAR ({len(critical_issues)}):")
                for i, issue in enumerate(critical_issues[:10], 1):
                    self.stdout.write(f"\n   {i}. [{issue.get('severity', '').upper()}] {issue.get('title', '')}")
                    desc = issue.get('description', '')
                    if len(desc) > 150:
                        desc = desc[:150] + '...'
                    self.stdout.write(f"      → {desc}")
            
            # Cleanup
            contract.delete()
            self.stdout.write(self.style.SUCCESS(f'\n✓ Test shartnoma o\'chirildi'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ XATOLIK: {e}'))
            import traceback
            traceback.print_exc()
            contract.delete()
