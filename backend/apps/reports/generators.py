"""
PDF Report generator for Legal Bridge AI.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from apps.contracts.models import Contract
from apps.analysis.models import AnalysisResult, ComplianceIssue


class PDFReportGenerator:
    """Generate PDF reports for contract analysis."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='TitleUz',
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='Heading1Uz',
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='Heading2Uz',
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyUz',
            fontSize=10,
            spaceBefore=5,
            spaceAfter=5,
            fontName='Helvetica'
        ))
    
    def generate_analysis_report(self, analysis: AnalysisResult) -> io.BytesIO:
        """Generate PDF report for analysis result."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        contract = analysis.contract
        
        # Title
        story.append(Paragraph(
            "SHARTNOMA TAHLILI HISOBOTI",
            self.styles['TitleUz']
        ))
        story.append(Spacer(1, 10*mm))
        
        # Contract info
        story.append(Paragraph("1. Shartnoma ma'lumotlari", self.styles['Heading1Uz']))
        
        contract_data = [
            ['Shartnoma raqami:', contract.contract_number or '-'],
            ['Shartnoma nomi:', contract.title or contract.original_filename],
            ['Shartnoma turi:', contract.get_contract_type_display()],
            ['1-tomon:', contract.party_a or '-'],
            ['2-tomon:', contract.party_b or '-'],
            ['Shartnoma sanasi:', str(contract.contract_date) if contract.contract_date else '-'],
            ['Summa:', f"{contract.total_amount} {contract.currency}" if contract.total_amount else '-'],
        ]
        
        table = Table(contract_data, colWidths=[50*mm, 110*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Spacer(1, 10*mm))
        
        # Risk score
        story.append(Paragraph("2. Xavf baholash", self.styles['Heading1Uz']))
        
        risk_color = colors.green
        if analysis.risk_level == 'medium':
            risk_color = colors.orange
        elif analysis.risk_level == 'high':
            risk_color = colors.red
        
        score_data = [
            ['Umumiy ball:', f"{analysis.overall_score}/100"],
            ['Xavf darajasi:', analysis.get_risk_level_display() if hasattr(analysis, 'get_risk_level_display') else analysis.risk_level],
            ['Qonunga moslik:', f"{analysis.compliance_score}/100"],
            ["To'liqlik:", f"{analysis.completeness_score}/100"],
            ['Aniqlik:', f"{analysis.clarity_score}/100"],
            ['Muvozanat:', f"{analysis.balance_score}/100"],
        ]
        
        score_table = Table(score_data, colWidths=[50*mm, 110*mm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 10*mm))
        
        # Summary
        if analysis.summary:
            story.append(Paragraph("3. Qisqacha tahlil", self.styles['Heading1Uz']))
            story.append(Paragraph(analysis.summary, self.styles['BodyUz']))
            story.append(Spacer(1, 10*mm))
        
        # Issues
        issues = analysis.issues.all()
        if issues:
            story.append(Paragraph("4. Aniqlangan muammolar", self.styles['Heading1Uz']))
            
            for i, issue in enumerate(issues, 1):
                severity_text = {
                    'critical': '⚠️ JIDDIY',
                    'high': '🔴 Yuqori',
                    'medium': '🟡 O\'rta',
                    'low': '🟢 Past',
                    'info': 'ℹ️ Ma\'lumot'
                }.get(issue.severity, issue.severity)
                
                story.append(Paragraph(
                    f"{i}. {issue.title} [{severity_text}]",
                    self.styles['Heading2Uz']
                ))
                story.append(Paragraph(issue.description, self.styles['BodyUz']))
                
                if issue.suggestion:
                    story.append(Paragraph(
                        f"<b>Tavsiya:</b> {issue.suggestion}",
                        self.styles['BodyUz']
                    ))
                
                if issue.law_name:
                    story.append(Paragraph(
                        f"<b>Qonun:</b> {issue.law_name}, {issue.law_article}",
                        self.styles['BodyUz']
                    ))
                
                story.append(Spacer(1, 5*mm))
        
        # Recommendations
        if analysis.recommendations:
            story.append(Paragraph("5. Tavsiyalar", self.styles['Heading1Uz']))
            for rec in analysis.recommendations:
                story.append(Paragraph(f"• {rec}", self.styles['BodyUz']))
        
        # Footer
        story.append(Spacer(1, 20*mm))
        story.append(Paragraph(
            f"Hisobot yaratilgan: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['BodyUz']
        ))
        story.append(Paragraph(
            "Legal Bridge AI - Avtomatlashtirilgan shartnoma tahlili tizimi",
            self.styles['BodyUz']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_compliance_report(self, contract: Contract, analysis: AnalysisResult) -> io.BytesIO:
        """Generate compliance-focused PDF report."""
        # Similar implementation for compliance report
        return self.generate_analysis_report(analysis)
    
    def generate_risk_report(self, contract: Contract, analysis: AnalysisResult) -> io.BytesIO:
        """Generate risk-focused PDF report."""
        # Similar implementation for risk report
        return self.generate_analysis_report(analysis)
