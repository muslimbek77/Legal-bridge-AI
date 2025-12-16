"""
Admin configuration for Contracts app.
"""

from django.contrib import admin
from .models import Contract, ContractSection, ContractClause, ContractVersion, ContractComment


class ContractSectionInline(admin.TabularInline):
    model = ContractSection
    extra = 0
    readonly_fields = ['section_type', 'title', 'is_compliant', 'risk_level']
    show_change_link = True


class ContractVersionInline(admin.TabularInline):
    model = ContractVersion
    extra = 0
    readonly_fields = ['version_number', 'created_by', 'created_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_number', 'title', 'contract_type', 'status',
        'party_a', 'party_b', 'uploaded_by', 'created_at'
    ]
    list_filter = ['status', 'contract_type', 'language', 'created_at']
    search_fields = ['contract_number', 'title', 'party_a', 'party_b', 'extracted_text']
    readonly_fields = [
        'id', 'extracted_text', 'is_scanned', 'ocr_confidence',
        'file_size', 'created_at', 'updated_at', 'analyzed_at'
    ]
    inlines = [ContractSectionInline, ContractVersionInline]
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    autocomplete_fields = ['uploaded_by', 'assigned_to']
    list_select_related = True
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('id', 'contract_number', 'title', 'contract_type', 'language', 'status')
        }),
        ('Fayl', {
            'fields': ('original_file', 'original_filename', 'file_type', 'file_size', 'is_scanned', 'ocr_confidence')
        }),
        ('Tomonlar', {
            'fields': ('party_a', 'party_a_inn', 'party_b', 'party_b_inn')
        }),
        ('Sanalar', {
            'fields': ('contract_date', 'start_date', 'end_date')
        }),
        ('Moliya', {
            'fields': ('total_amount', 'currency')
        }),
        ('Foydalanuvchilar', {
            'fields': ('uploaded_by', 'assigned_to')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'extracted_text')
        }),
        ('Vaqtlar', {
            'fields': ('created_at', 'updated_at', 'analyzed_at')
        }),
    )


@admin.register(ContractSection)
class ContractSectionAdmin(admin.ModelAdmin):
    list_display = ['contract', 'section_type', 'title', 'is_compliant', 'risk_level', 'order']
    list_filter = ['section_type', 'is_compliant', 'risk_level']
    search_fields = ['contract__title', 'title', 'content']
    readonly_fields = ['created_at']


@admin.register(ContractClause)
class ContractClauseAdmin(admin.ModelAdmin):
    list_display = ['section', 'clause_number', 'is_standard', 'is_one_sided', 'is_risky']
    list_filter = ['is_standard', 'is_one_sided', 'is_risky']
    search_fields = ['content', 'related_law']
    readonly_fields = ['created_at']


@admin.register(ContractVersion)
class ContractVersionAdmin(admin.ModelAdmin):
    list_display = ['contract', 'version_number', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['contract__title', 'changes_description']
    readonly_fields = ['created_at']


@admin.register(ContractComment)
class ContractCommentAdmin(admin.ModelAdmin):
    list_display = ['contract', 'user', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['contract__title', 'content']
    readonly_fields = ['created_at', 'updated_at']
