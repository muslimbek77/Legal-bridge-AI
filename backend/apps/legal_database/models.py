"""
Legal Database models for storing Uzbekistan laws and regulations.
"""

from django.db import models


class Law(models.Model):
    """
    Law or legal act (Qonun yoki huquqiy hujjat).
    """
    
    class LawType(models.TextChoices):
        CODE = 'code', 'Kodeks'
        LAW = 'law', 'Qonun'
        DECREE = 'decree', 'Farmon'
        RESOLUTION = 'resolution', 'Qaror'
        REGULATION = 'regulation', 'Nizom'
        INSTRUCTION = 'instruction', 'Yo\'riqnoma'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Amalda'
        AMENDED = 'amended', 'O\'zgartirilgan'
        REPEALED = 'repealed', 'Bekor qilingan'
    
    name = models.CharField('Nomi', max_length=500)
    name_ru = models.CharField('Nomi (rus)', max_length=500, blank=True)
    short_name = models.CharField('Qisqa nomi', max_length=100, blank=True)
    
    law_type = models.CharField(
        'Turi',
        max_length=20,
        choices=LawType.choices,
        default=LawType.LAW
    )
    
    number = models.CharField('Raqami', max_length=50, blank=True)
    adoption_date = models.DateField('Qabul qilingan sana', null=True, blank=True)
    effective_date = models.DateField('Kuchga kirgan sana', null=True, blank=True)
    
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    description = models.TextField('Tavsif', blank=True)
    source_url = models.URLField('Manba URL', blank=True)
    
    # For vector search
    is_indexed = models.BooleanField('Indekslangan', default=False)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'Qonun'
        verbose_name_plural = 'Qonunlar'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.short_name or self.name}"


class LawChapter(models.Model):
    """
    Chapter of a law (Bob).
    """
    
    law = models.ForeignKey(
        Law,
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name='Qonun'
    )
    number = models.CharField('Raqami', max_length=20)
    title = models.CharField('Nomi', max_length=500)
    title_ru = models.CharField('Nomi (rus)', max_length=500, blank=True)
    order = models.PositiveIntegerField('Tartib', default=0)
    
    class Meta:
        verbose_name = 'Bob'
        verbose_name_plural = 'Boblar'
        ordering = ['law', 'order']
    
    def __str__(self):
        return f"{self.law.short_name} - Bob {self.number}: {self.title}"


class LawArticle(models.Model):
    """
    Article of a law (Modda).
    """
    
    law = models.ForeignKey(
        Law,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Qonun'
    )
    chapter = models.ForeignKey(
        LawChapter,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='Bob'
    )
    
    number = models.CharField('Raqami', max_length=20)
    title = models.CharField('Nomi', max_length=500)
    title_ru = models.CharField('Nomi (rus)', max_length=500, blank=True)
    
    content = models.TextField('Mazmuni')
    content_ru = models.TextField('Mazmuni (rus)', blank=True)
    
    # For contract analysis
    is_mandatory = models.BooleanField('Majburiy', default=False)
    applies_to = models.JSONField(
        'Qo\'llaniladi',
        default=list,
        blank=True,
        help_text='Qaysi shartnoma turlariga tegishli'
    )
    
    # Keywords for search
    keywords = models.JSONField('Kalit so\'zlar', default=list, blank=True)
    
    # Vector embedding
    embedding = models.BinaryField('Embedding', null=True, blank=True)
    
    order = models.PositiveIntegerField('Tartib', default=0)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'Modda'
        verbose_name_plural = 'Moddalar'
        ordering = ['law', 'order']
    
    def __str__(self):
        return f"{self.law.short_name} - {self.number}-modda: {self.title}"


class LegalRule(models.Model):
    """
    Specific legal rules extracted from laws for contract validation.
    These are used by the Legal Compliance Engine.
    """
    
    class RuleType(models.TextChoices):
        MANDATORY_CLAUSE = 'mandatory_clause', 'Majburiy band'
        PROHIBITED_CLAUSE = 'prohibited_clause', 'Taqiqlangan band'
        RECOMMENDED_CLAUSE = 'recommended_clause', 'Tavsiya etilgan band'
        FORMAT_RULE = 'format_rule', 'Format talabi'
        PARTY_RULE = 'party_rule', 'Tomon talabi'
        TERM_RULE = 'term_rule', 'Muddat talabi'
        PAYMENT_RULE = 'payment_rule', 'To\'lov talabi'
    
    class Severity(models.TextChoices):
        CRITICAL = 'critical', 'Jiddiy'
        HIGH = 'high', 'Yuqori'
        MEDIUM = 'medium', 'O\'rta'
        LOW = 'low', 'Past'
    
    article = models.ForeignKey(
        LawArticle,
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name='Modda'
    )
    
    rule_type = models.CharField(
        'Qoida turi',
        max_length=30,
        choices=RuleType.choices
    )
    severity = models.CharField(
        'Jiddiylik',
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    
    title = models.CharField('Nomi', max_length=500)
    description = models.TextField('Tavsif')
    
    # Rule conditions
    condition = models.TextField('Shart', help_text='Qoida qachon qo\'llaniladi')
    validation_pattern = models.TextField(
        'Tekshirish patterni',
        blank=True,
        help_text='Regex yoki AI prompt'
    )
    
    # Applies to specific contract types
    applies_to_contract_types = models.JSONField(
        'Shartnoma turlari',
        default=list,
        blank=True
    )
    
    # Suggestion when rule is violated
    suggestion_template = models.TextField('Tavsiya shabloni', blank=True)
    
    is_active = models.BooleanField('Faol', default=True)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'Huquqiy qoida'
        verbose_name_plural = 'Huquqiy qoidalar'
        ordering = ['article', 'severity']
    
    def __str__(self):
        return f"{self.article.law.short_name} - {self.title}"


class ContractTemplate(models.Model):
    """
    Standard contract templates for reference.
    """
    
    name = models.CharField('Nomi', max_length=500)
    contract_type = models.CharField('Shartnoma turi', max_length=50)
    description = models.TextField('Tavsif', blank=True)
    
    template_file = models.FileField('Shablon fayli', upload_to='templates/', null=True, blank=True)
    template_text = models.TextField('Shablon matni', blank=True)
    
    # Required sections
    required_sections = models.JSONField('Majburiy bo\'limlar', default=list)
    
    # Associated laws
    related_laws = models.ManyToManyField(
        Law,
        related_name='templates',
        blank=True,
        verbose_name='Tegishli qonunlar'
    )
    
    is_approved = models.BooleanField('Tasdiqlangan', default=False)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'Shartnoma shabloni'
        verbose_name_plural = 'Shartnoma shablonlari'
        ordering = ['name']
    
    def __str__(self):
        return self.name
