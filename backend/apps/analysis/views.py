"""
Views for Analysis app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import AnalysisResult, ComplianceIssue, AnalysisFeedback
from .serializers import (
    AnalysisResultListSerializer,
    AnalysisResultDetailSerializer,
    ComplianceIssueSerializer,
    AnalysisFeedbackSerializer,
    AnalysisRequestSerializer,
    IssueResolveSerializer,
)
from .tasks import analyze_contract_task


class AnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for analysis results."""
    
    queryset = AnalysisResult.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'status', 'risk_level']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AnalysisResultListSerializer
        return AnalysisResultDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = AnalysisResult.objects.select_related('contract')
        
        if not user.is_admin:
            queryset = queryset.filter(
                contract__uploaded_by=user
            ) | queryset.filter(
                contract__assigned_to=user
            )
        
        return queryset.distinct()
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Start analysis for a contract."""
        serializer = AnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract_id = str(serializer.validated_data['contract_id'])
        
        # Check if contract exists and user has access
        from apps.contracts.models import Contract
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Shartnoma topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if analysis is already in progress
        existing = AnalysisResult.objects.filter(
            contract=contract,
            status=AnalysisResult.AnalysisStatus.IN_PROGRESS
        ).exists()
        
        if existing:
            return Response(
                {'error': 'Tahlil allaqachon jarayonda'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async task
        task = analyze_contract_task.delay(contract_id)
        
        return Response({
            'message': 'Tahlil boshlandi',
            'task_id': task.id,
            'contract_id': contract_id
        })
    
    @action(detail=True, methods=['get'])
    def issues(self, request, pk=None):
        """Get all issues for an analysis."""
        analysis = self.get_object()
        issues = analysis.issues.all()
        serializer = ComplianceIssueSerializer(issues, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get analysis summary."""
        analysis = self.get_object()
        
        issues_by_severity = {}
        for severity in ComplianceIssue.Severity.choices:
            issues_by_severity[severity[0]] = analysis.issues.filter(
                severity=severity[0]
            ).count()
        
        issues_by_type = {}
        for issue_type in ComplianceIssue.IssueType.choices:
            issues_by_type[issue_type[0]] = analysis.issues.filter(
                issue_type=issue_type[0]
            ).count()
        
        return Response({
            'overall_score': analysis.overall_score,
            'risk_level': analysis.risk_level,
            'scores': {
                'compliance': analysis.compliance_score,
                'completeness': analysis.completeness_score,
                'clarity': analysis.clarity_score,
                'balance': analysis.balance_score,
            },
            'issues_count': analysis.issues.count(),
            'issues_by_severity': issues_by_severity,
            'issues_by_type': issues_by_type,
            'summary': analysis.summary,
            'recommendations': analysis.recommendations,
        })


class ComplianceIssueViewSet(viewsets.ModelViewSet):
    """ViewSet for compliance issues."""
    
    queryset = ComplianceIssue.objects.all()
    serializer_class = ComplianceIssueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['analysis', 'issue_type', 'severity', 'is_resolved']
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark issue as resolved."""
        issue = self.get_object()
        serializer = IssueResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        issue.is_resolved = True
        issue.resolved_by = request.user
        issue.resolution_notes = serializer.validated_data.get('resolution_notes', '')
        issue.save()
        
        return Response({
            'message': 'Muammo hal qilindi deb belgilandi',
            'issue_id': str(issue.id)
        })
    
    @action(detail=True, methods=['post'])
    def unresolve(self, request, pk=None):
        """Mark issue as unresolved."""
        issue = self.get_object()
        issue.is_resolved = False
        issue.resolved_by = None
        issue.resolution_notes = ''
        issue.save()
        
        return Response({
            'message': 'Muammo qayta ochildi',
            'issue_id': str(issue.id)
        })


class AnalysisFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for analysis feedback."""
    
    queryset = AnalysisFeedback.objects.all()
    serializer_class = AnalysisFeedbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['analysis', 'feedback_type', 'user']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get feedback statistics for model improvement."""
        total = AnalysisFeedback.objects.count()
        
        stats = {
            'total': total,
            'by_type': {},
            'used_for_training': AnalysisFeedback.objects.filter(
                is_used_for_training=True
            ).count()
        }
        
        for feedback_type in AnalysisFeedback.FeedbackType.choices:
            stats['by_type'][feedback_type[0]] = AnalysisFeedback.objects.filter(
                feedback_type=feedback_type[0]
            ).count()
        
        return Response(stats)
