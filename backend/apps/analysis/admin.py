"""
Admin configuration for Analysis app.
"""

from django.contrib import admin
from .models import AnalysisResult, ComplianceIssue, LawReference, AnalysisFeedback


class ComplianceIssueInline(admin.TabularInline):
    model = ComplianceIssue
    extra = 0
    readonly_fields = ['issue_type', 'severity', 'title', 'is_resolved']
    show_change_link = True


class LawReferenceInline(admin.TabularInline):
    model = LawReference
    extra = 0
    readonly_fields = ['law_name', 'article_number']


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'status', 'overall_score', 'risk_level',
        'processing_time', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'risk_level', 'created_at']
    search_fields = ['contract__title', 'summary']
    readonly_fields = [
        'id', 'processing_time', 'error_message',
        'created_at', 'completed_at'
    ]
    inlines = [ComplianceIssueInline, LawReferenceInline]
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    autocomplete_fields = ['contract']
    list_select_related = True
    fieldsets = (
        ('Asosiy', {
            'fields': ('id', 'contract', 'status')
        }),
        ('Ballar', {
            'fields': (
                'overall_score', 'risk_level', 'compliance_score',
                'completeness_score', 'clarity_score', 'balance_score'
            )
        }),
        ('Natijalar', {
            'fields': ('summary', 'recommendations')
        }),
        ('Texnik', {
            'fields': ('processing_time', 'error_message', 'model_used', 'model_version')
        }),
        ('Vaqtlar', {
            'fields': ('created_at', 'completed_at')
        }),
    )


@admin.register(ComplianceIssue)
class ComplianceIssueAdmin(admin.ModelAdmin):
    list_display = [
        'analysis', 'issue_type', 'severity', 'title',
        'is_resolved', 'created_at'
    ]
    list_filter = ['issue_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['title', 'description', 'law_name']
    readonly_fields = ['created_at']


@admin.register(LawReference)
class LawReferenceAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'law_name', 'article_number', 'created_at']
    list_filter = ['law_name', 'created_at']
    search_fields = ['law_name', 'article_number', 'article_text']
    readonly_fields = ['created_at']


@admin.register(AnalysisFeedback)
class AnalysisFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'analysis', 'user', 'feedback_type',
        'is_used_for_training', 'created_at'
    ]
    list_filter = ['feedback_type', 'is_used_for_training', 'created_at']
    search_fields = ['comment', 'correct_answer']
    readonly_fields = ['created_at']
