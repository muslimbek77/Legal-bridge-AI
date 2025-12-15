"""
Report generation models.
"""

import uuid
from django.db import models
from django.conf import settings
from apps.contracts.models import Contract
from apps.analysis.models import AnalysisResult


def report_upload_path(instance, filename):
    return f'reports/{instance.id}/{filename}'


class Report(models.Model):
    """Generated reports for contracts and analyses."""
    
    class ReportType(models.TextChoices):
        ANALYSIS = 'analysis', 'Tahlil hisoboti'
        COMPLIANCE = 'compliance', 'Qonunga moslik hisoboti'
        RISK = 'risk', 'Xavf hisoboti'
        SUMMARY = 'summary', 'Qisqacha hisobot'
        FULL = 'full', 'To\'liq hisobot'
    
    class Format(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'Word'
        HTML = 'html', 'HTML'
        JSON = 'json', 'JSON'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Shartnoma'
    )
    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name='Tahlil'
    )
    
    report_type = models.CharField(
        'Hisobot turi',
        max_length=20,
        choices=ReportType.choices,
        default=ReportType.FULL
    )
    report_format = models.CharField(
        'Format',
        max_length=10,
        choices=Format.choices,
        default=Format.PDF
    )
    
    title = models.CharField('Sarlavha', max_length=500)
    file = models.FileField('Fayl', upload_to=report_upload_path, null=True, blank=True)
    file_size = models.PositiveIntegerField('Fayl hajmi', default=0)
    
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name='Yaratgan'
    )
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Hisobot'
        verbose_name_plural = 'Hisobotlar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract} - {self.get_report_type_display()}"
