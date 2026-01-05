"""
Admin configuration for Legal Database app.
"""

from django.contrib import admin
from .models import Law, LawChapter, LawArticle, LegalRule, ContractTemplate


class LawChapterInline(admin.TabularInline):
    model = LawChapter
    extra = 0


class LawArticleInline(admin.TabularInline):
    model = LawArticle
    extra = 0
    show_change_link = True
    fields = ['number', 'title', 'is_mandatory', 'order']


class LegalRuleInline(admin.TabularInline):
    model = LegalRule
    extra = 0


@admin.register(Law)
class LawAdmin(admin.ModelAdmin):
    list_display = ['short_name', 'name', 'law_type', 'status', 'adoption_date', 'is_indexed']
    list_filter = ['law_type', 'status', 'is_indexed']
    search_fields = ['name', 'name_ru', 'short_name']
    inlines = [LawChapterInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LawChapter)
class LawChapterAdmin(admin.ModelAdmin):
    list_display = ['law', 'number', 'title', 'order']
    list_filter = ['law']
    search_fields = ['title', 'title_ru']
    inlines = [LawArticleInline]


@admin.register(LawArticle)
class LawArticleAdmin(admin.ModelAdmin):
    list_display = ['law', 'number', 'title', 'is_mandatory', 'order']
    list_filter = ['law', 'is_mandatory']
    search_fields = ['title', 'title_ru', 'content']
    inlines = [LegalRuleInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LegalRule)
class LegalRuleAdmin(admin.ModelAdmin):
    list_display = ['article', 'title', 'rule_type', 'severity', 'is_active']
    list_filter = ['rule_type', 'severity', 'is_active']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'contract_type', 'is_approved', 'created_at']
    list_filter = ['contract_type', 'is_approved']
    search_fields = ['name', 'description']
    filter_horizontal = ['related_laws']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
