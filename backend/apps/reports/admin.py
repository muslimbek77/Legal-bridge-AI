"""
Admin configuration for Reports app.
"""

from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['contract', 'report_type', 'report_format', 'generated_by', 'created_at']
    list_filter = ['report_type', 'report_format', 'created_at']
    search_fields = ['contract__title', 'title']
    readonly_fields = ['id', 'file_size', 'created_at']
