"""
Serializers for Reports app.
"""

from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for reports."""
    
    contract_title = serializers.CharField(source='contract.title', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    risk_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'contract', 'contract_title', 'analysis',
            'report_type', 'report_type_display', 'format', 'format_display',
            'title', 'file', 'file_size', 'generated_by', 'generated_by_name',
            'created_at', 'risk_score'
        ]
        read_only_fields = ['id', 'file', 'file_size', 'generated_by', 'created_at']
    
    def get_risk_score(self, obj):
        """Get risk score from related analysis or contract's latest analysis."""
        if obj.analysis and obj.analysis.overall_score is not None:
            return obj.analysis.overall_score
        # Fallback: get from contract's latest analysis
        latest_analysis = obj.contract.analyses.filter(status='completed').order_by('-created_at').first()
        if latest_analysis:
            return latest_analysis.overall_score
        return 0


class GenerateReportSerializer(serializers.Serializer):
    """Serializer for report generation request."""
    
    contract_id = serializers.UUIDField()
    report_type = serializers.ChoiceField(choices=Report.ReportType.choices)
    format = serializers.ChoiceField(choices=Report.Format.choices, default='pdf')
