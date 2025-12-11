"""
Custom User model for Legal Bridge AI.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email manzil majburiy')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi kerak')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi kerak')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model with extended fields for legal professionals.
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        LAWYER = 'lawyer', 'Yurist'
        ANALYST = 'analyst', 'Tahlilchi'
        MANAGER = 'manager', 'Menejer'
        VIEWER = 'viewer', 'Foydalanuvchi'
    
    username = None  # Remove username, use email instead
    email = models.EmailField('Email manzil', unique=True)
    
    # Profile fields
    first_name = models.CharField('Ism', max_length=150)
    last_name = models.CharField('Familiya', max_length=150)
    middle_name = models.CharField('Otasining ismi', max_length=150, blank=True)
    phone = models.CharField('Telefon raqam', max_length=20, blank=True)
    
    # Organization
    organization = models.CharField('Tashkilot nomi', max_length=255, blank=True)
    position = models.CharField('Lavozim', max_length=255, blank=True)
    department = models.CharField('Bo\'lim', max_length=255, blank=True)
    
    # Role and permissions
    role = models.CharField(
        'Rol',
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )
    
    # Settings
    preferred_language = models.CharField(
        'Til',
        max_length=10,
        choices=[
            ('uz-latn', 'O\'zbek (lotin)'),
            ('uz-cyrl', 'Ўзбек (кирилл)'),
            ('ru', 'Русский'),
        ],
        default='uz-latn'
    )
    
    # Timestamps
    created_at = models.DateTimeField('Yaratilgan vaqt', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan vaqt', auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return full name with middle name."""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_lawyer(self):
        return self.role == self.Role.LAWYER
    
    @property
    def can_analyze(self):
        """Check if user can run contract analysis."""
        return self.role in [self.Role.ADMIN, self.Role.LAWYER, self.Role.ANALYST]
    
    @property
    def can_approve(self):
        """Check if user can approve contracts."""
        return self.role in [self.Role.ADMIN, self.Role.LAWYER, self.Role.MANAGER]


class UserActivity(models.Model):
    """Track user activities for audit."""
    
    class ActionType(models.TextChoices):
        LOGIN = 'login', 'Kirish'
        LOGOUT = 'logout', 'Chiqish'
        UPLOAD = 'upload', 'Fayl yuklash'
        ANALYZE = 'analyze', 'Tahlil qilish'
        APPROVE = 'approve', 'Tasdiqlash'
        EXPORT = 'export', 'Eksport'
        VIEW = 'view', 'Ko\'rish'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Foydalanuvchi'
    )
    action = models.CharField(
        'Harakat',
        max_length=20,
        choices=ActionType.choices
    )
    description = models.TextField('Tavsif', blank=True)
    ip_address = models.GenericIPAddressField('IP manzil', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    metadata = models.JSONField('Qo\'shimcha ma\'lumotlar', default=dict, blank=True)
    created_at = models.DateTimeField('Vaqt', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Foydalanuvchi faoliyati'
        verbose_name_plural = 'Foydalanuvchi faoliyatlari'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} - {self.created_at}"
