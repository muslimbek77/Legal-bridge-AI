"""Legal Database app configuration."""
from django.apps import AppConfig

class LegalDatabaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.legal_database'
    verbose_name = 'Qonunlar bazasi'
