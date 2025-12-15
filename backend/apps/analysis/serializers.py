"""
Serializers for Analysis app.
"""

from rest_framework import serializers
from .models import AnalysisResult, ComplianceIssue, LawReference, AnalysisFeedback


class LawReferenceSerializer(serializers.ModelSerializer):
    """Serializer for law references."""
    
    class Meta:
        model = LawReference
        fields = [
            'id', 'law_name', 'article_number', 'article_title',
            'article_text', 'relevance_reason'
        ]


class ComplianceIssueSerializer(serializers.ModelSerializer):
    """Serializer for compliance issues."""
    
    issue_type_display = serializers.CharField(source='get_issue_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    contract_id = serializers.UUIDField(source='analysis.contract.id', read_only=True)
    contract_title = serializers.CharField(source='analysis.contract.title', read_only=True)
    
    class Meta:
        model = ComplianceIssue
        fields = [
            'id', 'analysis', 'contract_id', 'contract_title',
            'issue_type', 'issue_type_display', 'severity', 'severity_display',
            'title', 'description', 'section_reference', 'clause_reference',
            'text_excerpt', 'law_name', 'law_article', 'law_text',
            'suggestion', 'suggested_text', 'is_resolved', 'resolved_by',
            'resolved_by_name', 'resolution_notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnalysisResultListSerializer(serializers.ModelSerializer):
    """Serializer for analysis result list."""
    
    contract_title = serializers.CharField(source='contract.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    issues_count = serializers.IntegerField(source='issues.count', read_only=True)
    
    class Meta:
        model = AnalysisResult
        fields = [
            'id', 'contract', 'contract_title', 'status', 'status_display',
            'overall_score', 'risk_level', 'issues_count',
            'created_at', 'completed_at'
        ]


class AnalysisResultDetailSerializer(serializers.ModelSerializer):
    """Serializer for analysis result detail."""
    
    contract_title = serializers.CharField(source='contract.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    issues = ComplianceIssueSerializer(many=True, read_only=True)
    law_references = LawReferenceSerializer(many=True, read_only=True)
    
    class Meta:
        model = AnalysisResult
        fields = [
            'id', 'contract', 'contract_title', 'status', 'status_display',
            'overall_score', 'risk_level', 'compliance_score', 'completeness_score',
            'clarity_score', 'balance_score', 'summary', 'recommendations',
            'processing_time', 'error_message', 'model_used', 'model_version',
            'created_at', 'completed_at', 'issues', 'law_references'
        ]


class AnalysisFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for analysis feedback."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    
    class Meta:
        model = AnalysisFeedback
        fields = [
            'id', 'analysis', 'issue', 'user', 'user_name',
            'feedback_type', 'feedback_type_display', 'comment',
            'correct_answer', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class AnalysisRequestSerializer(serializers.Serializer):
    """Serializer for analysis request."""
    
    contract_id = serializers.UUIDField()
    analyze_compliance = serializers.BooleanField(default=True)
    analyze_risks = serializers.BooleanField(default=True)
    analyze_clauses = serializers.BooleanField(default=True)
    language = serializers.ChoiceField(
        choices=['uz-latn', 'uz-cyrl', 'ru', 'auto'],
        default='auto'
    )


class IssueResolveSerializer(serializers.Serializer):
    """Serializer for resolving issues."""
    
    resolution_notes = serializers.CharField(required=False, allow_blank=True)
