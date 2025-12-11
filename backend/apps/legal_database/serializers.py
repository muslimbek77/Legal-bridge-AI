"""
Serializers for Legal Database app.
"""

from rest_framework import serializers
from .models import Law, LawChapter, LawArticle, LegalRule, ContractTemplate


class LegalRuleSerializer(serializers.ModelSerializer):
    """Serializer for legal rules."""
    
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = LegalRule
        fields = [
            'id', 'rule_type', 'rule_type_display', 'severity', 'severity_display',
            'title', 'description', 'condition', 'validation_pattern',
            'applies_to_contract_types', 'suggestion_template', 'is_active'
        ]


class LawArticleSerializer(serializers.ModelSerializer):
    """Serializer for law articles."""
    
    rules = LegalRuleSerializer(many=True, read_only=True)
    law_name = serializers.CharField(source='law.short_name', read_only=True)
    
    class Meta:
        model = LawArticle
        fields = [
            'id', 'law', 'law_name', 'chapter', 'number', 'title', 'title_ru',
            'content', 'content_ru', 'is_mandatory', 'applies_to', 'keywords',
            'order', 'rules'
        ]


class LawChapterSerializer(serializers.ModelSerializer):
    """Serializer for law chapters."""
    
    articles = LawArticleSerializer(many=True, read_only=True)
    
    class Meta:
        model = LawChapter
        fields = ['id', 'number', 'title', 'title_ru', 'order', 'articles']


class LawListSerializer(serializers.ModelSerializer):
    """Serializer for law list."""
    
    law_type_display = serializers.CharField(source='get_law_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    articles_count = serializers.IntegerField(source='articles.count', read_only=True)
    
    class Meta:
        model = Law
        fields = [
            'id', 'name', 'short_name', 'law_type', 'law_type_display',
            'number', 'adoption_date', 'status', 'status_display',
            'articles_count', 'is_indexed'
        ]


class LawDetailSerializer(serializers.ModelSerializer):
    """Serializer for law detail."""
    
    chapters = LawChapterSerializer(many=True, read_only=True)
    law_type_display = serializers.CharField(source='get_law_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Law
        fields = [
            'id', 'name', 'name_ru', 'short_name', 'law_type', 'law_type_display',
            'number', 'adoption_date', 'effective_date', 'status', 'status_display',
            'description', 'source_url', 'is_indexed', 'chapters',
            'created_at', 'updated_at'
        ]


class ContractTemplateSerializer(serializers.ModelSerializer):
    """Serializer for contract templates."""
    
    related_laws = LawListSerializer(many=True, read_only=True)
    
    class Meta:
        model = ContractTemplate
        fields = [
            'id', 'name', 'contract_type', 'description', 'template_file',
            'template_text', 'required_sections', 'related_laws', 'is_approved',
            'created_at', 'updated_at'
        ]


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for search queries."""
    
    query = serializers.CharField(max_length=500)
    law_types = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    contract_type = serializers.CharField(required=False)
    limit = serializers.IntegerField(default=10, max_value=50)
