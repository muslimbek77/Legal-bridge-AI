"""
Analysis models for Legal Bridge AI.
"""

import uuid
from django.db import models
from django.conf import settings
from apps.contracts.models import Contract


class AnalysisResult(models.Model):
    """
    Stores the complete analysis result for a contract.
    """
    
    class AnalysisStatus(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        IN_PROGRESS = 'in_progress', 'Jarayonda'
        COMPLETED = 'completed', 'Tugallandi'
        FAILED = 'failed', 'Xatolik'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='analyses',
        verbose_name='Shartnoma'
    )
    
    # Analysis status
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.PENDING
    )
    
    # Risk scoring (0-100)
    overall_score = models.IntegerField('Umumiy ball', default=0)
    risk_level = models.CharField(
        'Xavf darajasi',
        max_length=20,
        choices=[
            ('low', 'Past (70-100)'),
            ('medium', 'O\'rta (30-70)'),
            ('high', 'Yuqori (0-30)'),
        ],
        default='medium'
    )
    
    # Detailed scores
    compliance_score = models.IntegerField('Qonunga moslik balli', default=0)
    completeness_score = models.IntegerField('To\'liqlik balli', default=0)
    clarity_score = models.IntegerField('Aniqlik balli', default=0)
    balance_score = models.IntegerField('Muvozanat balli', default=0)
    
    # Summary
    summary = models.TextField('Qisqacha tahlil', blank=True)
    recommendations = models.JSONField('Tavsiyalar', default=list)
    
    # Processing info
    processing_time = models.FloatField('Qayta ishlash vaqti (soniya)', null=True, blank=True)
    error_message = models.TextField('Xatolik xabari', blank=True)
    
    # AI model info
    model_used = models.CharField('Ishlatilgan model', max_length=255, blank=True)
    model_version = models.CharField('Model versiyasi', max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    completed_at = models.DateTimeField('Tugallangan', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Tahlil natijasi'
        verbose_name_plural = 'Tahlil natijalari'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract} - {self.overall_score} ball"
    
    def calculate_risk_level(self):
        """Calculate risk level based on overall score."""
        if self.overall_score >= 70:
            return 'low'
        elif self.overall_score >= 30:
            return 'medium'
        return 'high'
    
    def save(self, *args, **kwargs):
        self.risk_level = self.calculate_risk_level()
        super().save(*args, **kwargs)


class ComplianceIssue(models.Model):
    """
    Individual compliance issues found in analysis.
    """
    
    class Severity(models.TextChoices):
        CRITICAL = 'critical', 'Jiddiy'
        HIGH = 'high', 'Yuqori'
        MEDIUM = 'medium', 'O\'rta'
        LOW = 'low', 'Past'
        INFO = 'info', 'Ma\'lumot'
    
    class IssueType(models.TextChoices):
        MISSING_CLAUSE = 'missing_clause', 'Yetishmayotgan band'
        INVALID_CLAUSE = 'invalid_clause', 'Noto\'g\'ri band'
        ONE_SIDED = 'one_sided', 'Bir tomonlama band'
        UNCLEAR = 'unclear', 'Noaniq band'
        CONFLICT = 'conflict', 'Ziddiyatli band'
        ILLEGAL = 'illegal', 'Noqonuniy band'
        MISSING_INFO = 'missing_info', 'Yetishmayotgan ma\'lumot'
        FORMAT = 'format', 'Format xatoligi'
        SPELLING = 'spelling', 'Imloviy xato'
        GRAMMAR = 'grammar', 'Grammatik xato'
        OTHER = 'other', 'Boshqa'
    
    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name='Tahlil'
    )
    
    # Issue details
    issue_type = models.CharField(
        'Muammo turi',
        max_length=30,
        choices=IssueType.choices
    )
    severity = models.CharField(
        'Jiddiylik',
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    title = models.CharField('Sarlavha', max_length=1000)
    description = models.TextField('Tavsif')
    
    # Location in contract
    section_reference = models.CharField('Bo\'lim', max_length=255, blank=True)
    clause_reference = models.CharField('Band', max_length=255, blank=True)
    text_excerpt = models.TextField('Matn bo\'lagi', blank=True)
    
    # Legal reference
    law_name = models.CharField('Qonun nomi', max_length=1000, blank=True)
    law_article = models.CharField('Qonun moddasi', max_length=255, blank=True)
    law_text = models.TextField('Qonun matni', blank=True)
    
    # Suggestion
    suggestion = models.TextField('Tavsiya', blank=True)
    suggested_text = models.TextField('Tavsiya etilgan matn', blank=True)
    
    # Status
    is_resolved = models.BooleanField('Hal qilingan', default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_issues',
        verbose_name='Hal qilgan'
    )
    resolution_notes = models.TextField('Hal qilish izohi', blank=True)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Muammo'
        verbose_name_plural = 'Muammolar'
        ordering = ['severity', '-created_at']
    
    def __str__(self):
        return f"{self.analysis.contract} - {self.title}"


class LawReference(models.Model):
    """
    Law references used in analysis.
    """
    
    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
        related_name='law_references',
        verbose_name='Tahlil'
    )
    
    law_name = models.CharField('Qonun nomi', max_length=500)
    article_number = models.CharField('Modda raqami', max_length=50)
    article_title = models.CharField('Modda nomi', max_length=500, blank=True)
    article_text = models.TextField('Modda matni')
    relevance_reason = models.TextField('Tegishlilik sababi', blank=True)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Qonun havolasi'
        verbose_name_plural = 'Qonun havolalari'
    
    def __str__(self):
        return f"{self.law_name} - {self.article_number}"


class AnalysisFeedback(models.Model):
    """
    Feedback from lawyers on analysis accuracy for model improvement.
    """
    
    class FeedbackType(models.TextChoices):
        CORRECT = 'correct', 'To\'g\'ri'
        PARTIALLY_CORRECT = 'partially_correct', 'Qisman to\'g\'ri'
        INCORRECT = 'incorrect', 'Noto\'g\'ri'
        MISSED = 'missed', 'O\'tkazib yuborilgan'
    
    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name='Tahlil'
    )
    issue = models.ForeignKey(
        ComplianceIssue,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='feedbacks',
        verbose_name='Muammo'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analysis_feedbacks',
        verbose_name='Foydalanuvchi'
    )
    
    feedback_type = models.CharField(
        'Baho turi',
        max_length=20,
        choices=FeedbackType.choices
    )
    comment = models.TextField('Izoh')
    correct_answer = models.TextField('To\'g\'ri javob', blank=True)
    
    # For training
    is_used_for_training = models.BooleanField('O\'qitish uchun ishlatilgan', default=False)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Teskari aloqa'
        verbose_name_plural = 'Teskari aloqalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.analysis.contract} - {self.user} - {self.get_feedback_type_display()}"
