"""
Contract models for Legal Bridge AI.
"""

import uuid
from django.db import models
from django.conf import settings


def contract_upload_path(instance, filename):
    """Generate upload path for contract files."""
    return f'contracts/{instance.id}/{filename}'


class Contract(models.Model):
    """
    Main contract model storing uploaded contracts and their metadata.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Qoralama'
        UPLOADED = 'uploaded', 'Yuklangan'
        PROCESSING = 'processing', 'Qayta ishlanmoqda'
        ANALYZED = 'analyzed', 'Tahlil qilingan'
        REVIEWED = 'reviewed', 'Ko\'rib chiqilgan'
        APPROVED = 'approved', 'Tasdiqlangan'
        REJECTED = 'rejected', 'Rad etilgan'
        ARCHIVED = 'archived', 'Arxivlangan'
    
    class ContractType(models.TextChoices):
        SERVICE = 'service', 'Xizmat ko\'rsatish shartnomasi'
        SUPPLY = 'supply', 'Mol yetkazib berish shartnomasi'
        WORK = 'work', 'Pudrat shartnomasi'
        LABOR = 'labor', 'Mehnat shartnomasi'
        LEASE = 'lease', 'Ijara shartnomasi'
        LOAN = 'loan', 'Qarz shartnomasi'
        AGENCY = 'agency', 'Agentlik shartnomasi'
        COMMISSION = 'commission', 'Komissiya shartnomasi'
        FRANCHISE = 'franchise', 'Franchayzing shartnomasi'
        PROCUREMENT = 'procurement', 'Davlat xaridi shartnomasi'
        OTHER = 'other', 'Boshqa'
    
    class Language(models.TextChoices):
        UZ_LATN = 'uz-latn', 'O\'zbek (lotin)'
        UZ_CYRL = 'uz-cyrl', 'Ўзбек (кирилл)'
        RU = 'ru', 'Русский'
        MIXED = 'mixed', 'Aralash'
    
    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_number = models.CharField('Shartnoma raqami', max_length=100, blank=True)
    
    # File information
    original_file = models.FileField('Asl fayl', upload_to=contract_upload_path)
    original_filename = models.CharField('Fayl nomi', max_length=255)
    file_type = models.CharField('Fayl turi', max_length=20)  # pdf, docx, jpg, etc.
    file_size = models.PositiveIntegerField('Fayl hajmi (bayt)', default=0)
    
    # Extracted content
    extracted_text = models.TextField('Ajratilgan matn', blank=True)
    is_scanned = models.BooleanField('Skanlangan hujjat', default=False)
    ocr_confidence = models.FloatField('OCR ishonchliligi', null=True, blank=True)
    
    # Contract metadata
    title = models.CharField('Shartnoma nomi', max_length=500, blank=True)
    contract_type = models.CharField(
        'Shartnoma turi',
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.OTHER
    )
    language = models.CharField(
        'Til',
        max_length=10,
        choices=Language.choices,
        default=Language.UZ_LATN
    )
    
    # Parties
    party_a = models.CharField('1-tomon', max_length=500, blank=True)
    party_a_inn = models.CharField('1-tomon INN', max_length=20, blank=True)
    party_b = models.CharField('2-tomon', max_length=500, blank=True)
    party_b_inn = models.CharField('2-tomon INN', max_length=20, blank=True)
    
    # Dates
    contract_date = models.DateField('Shartnoma sanasi', null=True, blank=True)
    start_date = models.DateField('Boshlanish sanasi', null=True, blank=True)
    end_date = models.DateField('Tugash sanasi', null=True, blank=True)
    
    # Financial
    total_amount = models.DecimalField(
        'Umumiy summa',
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField('Valyuta', max_length=10, default='UZS')
    
    # Status and workflow
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED
    )
    
    # Users
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_contracts',
        verbose_name='Yuklagan'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_contracts',
        verbose_name='Tayinlangan'
    )
    
    # Notes
    notes = models.TextField('Izohlar', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    analyzed_at = models.DateTimeField('Tahlil qilingan', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Shartnoma'
        verbose_name_plural = 'Shartnomalar'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.contract_number:
            return f"{self.contract_number} - {self.title or self.original_filename}"
        return self.title or self.original_filename
    
    @property
    def is_analyzed(self):
        return self.status in [self.Status.ANALYZED, self.Status.REVIEWED, self.Status.APPROVED]


class ContractSection(models.Model):
    """
    Parsed sections of a contract.
    """
    
    class SectionType(models.TextChoices):
        HEADER = 'header', 'Sarlavha'
        PARTIES = 'parties', 'Tomonlar'
        SUBJECT = 'subject', 'Shartnoma predmeti'
        RIGHTS = 'rights', 'Huquqlar'
        OBLIGATIONS = 'obligations', 'Majburiyatlar'
        PRICE = 'price', 'Narx va to\'lov'
        DELIVERY = 'delivery', 'Yetkazib berish'
        QUALITY = 'quality', 'Sifat talablari'
        WARRANTY = 'warranty', 'Kafolat'
        LIABILITY = 'liability', 'Javobgarlik'
        FORCE_MAJEURE = 'force_majeure', 'Fors-major'
        DISPUTE = 'dispute', 'Nizolarni hal qilish'
        TERM = 'term', 'Muddat'
        TERMINATION = 'termination', 'Bekor qilish'
        CONFIDENTIAL = 'confidential', 'Maxfiylik'
        ADDITIONAL = 'additional', 'Qo\'shimcha shartlar'
        REQUISITES = 'requisites', 'Rekvizitlar'
        SIGNATURES = 'signatures', 'Imzolar'
        OTHER = 'other', 'Boshqa'
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Shartnoma'
    )
    section_type = models.CharField(
        'Bo\'lim turi',
        max_length=30,
        choices=SectionType.choices
    )
    section_number = models.CharField('Bo\'lim raqami', max_length=20, blank=True)
    title = models.CharField('Sarlavha', max_length=500, blank=True)
    content = models.TextField('Mazmun')
    start_position = models.PositiveIntegerField('Boshlanish pozitsiyasi', default=0)
    end_position = models.PositiveIntegerField('Tugash pozitsiyasi', default=0)
    order = models.PositiveIntegerField('Tartib', default=0)
    
    # Analysis results
    is_compliant = models.BooleanField('Qonunga mos', null=True)
    risk_level = models.CharField(
        'Xavf darajasi',
        max_length=20,
        choices=[
            ('low', 'Past'),
            ('medium', 'O\'rta'),
            ('high', 'Yuqori'),
        ],
        blank=True
    )
    issues = models.JSONField('Muammolar', default=list, blank=True)
    suggestions = models.JSONField('Tavsiyalar', default=list, blank=True)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Shartnoma bo\'limi'
        verbose_name_plural = 'Shartnoma bo\'limlari'
        ordering = ['contract', 'order']
    
    def __str__(self):
        return f"{self.contract} - {self.get_section_type_display()}"


class ContractClause(models.Model):
    """
    Individual clauses within contract sections.
    """
    
    section = models.ForeignKey(
        ContractSection,
        on_delete=models.CASCADE,
        related_name='clauses',
        verbose_name='Bo\'lim'
    )
    clause_number = models.CharField('Band raqami', max_length=20, blank=True)
    content = models.TextField('Mazmun')
    
    # Analysis
    is_standard = models.BooleanField('Standart band', default=True)
    is_one_sided = models.BooleanField('Bir tomonlama', default=False)
    is_risky = models.BooleanField('Xavfli', default=False)
    risk_description = models.TextField('Xavf tavsifi', blank=True)
    
    # Legal reference
    related_law = models.CharField('Tegishli qonun', max_length=500, blank=True)
    law_article = models.CharField('Qonun moddasi', max_length=100, blank=True)
    
    order = models.PositiveIntegerField('Tartib', default=0)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Shartnoma bandi'
        verbose_name_plural = 'Shartnoma bandlari'
        ordering = ['section', 'order']
    
    def __str__(self):
        return f"{self.section.contract} - {self.clause_number}"


class ContractVersion(models.Model):
    """
    Version history for contracts.
    """
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='Shartnoma'
    )
    version_number = models.PositiveIntegerField('Versiya raqami')
    file = models.FileField('Fayl', upload_to=contract_upload_path)
    changes_description = models.TextField('O\'zgarishlar tavsifi', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Yaratgan'
    )
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Shartnoma versiyasi'
        verbose_name_plural = 'Shartnoma versiyalari'
        ordering = ['contract', '-version_number']
        unique_together = ['contract', 'version_number']
    
    def __str__(self):
        return f"{self.contract} - v{self.version_number}"


class ContractComment(models.Model):
    """
    Comments on contracts for collaboration.
    """
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Shartnoma'
    )
    section = models.ForeignKey(
        ContractSection,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
        verbose_name='Bo\'lim'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contract_comments',
        verbose_name='Foydalanuvchi'
    )
    content = models.TextField('Izoh')
    is_resolved = models.BooleanField('Hal qilingan', default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_comments',
        verbose_name='Hal qilgan'
    )
    resolved_at = models.DateTimeField('Hal qilingan vaqt', null=True, blank=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'Shartnoma izohi'
        verbose_name_plural = 'Shartnoma izohlari'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract} - {self.user} - {self.created_at}"
