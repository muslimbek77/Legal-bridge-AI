"""
Views for Analysis app.
"""

import sys
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

# Add ai_engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

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
        # Use detail serializer when filtering by contract (single result expected)
        if self.request.query_params.get('contract'):
            return AnalysisResultDetailSerializer
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
    from rest_framework import filters
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['analysis', 'issue_type', 'severity', 'is_resolved']
    search_fields = ['title', 'description']
    
    def get_queryset(self):
        user = self.request.user
        queryset = ComplianceIssue.objects.select_related('analysis', 'analysis__contract')
        
        if not user.is_admin:
            queryset = queryset.filter(
                analysis__contract__uploaded_by=user
            ) | queryset.filter(
                analysis__contract__assigned_to=user
            )
        
        return queryset.distinct().order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get compliance issues statistics."""
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset()
        
        # Severity bo'yicha
        by_severity = {}
        for severity in ComplianceIssue.Severity.choices:
            by_severity[severity[0]] = queryset.filter(severity=severity[0]).count()
        
        # Type bo'yicha
        by_type = {}
        for issue_type in ComplianceIssue.IssueType.choices:
            by_type[issue_type[0]] = queryset.filter(issue_type=issue_type[0]).count()
        
        # Oylik trend (so'nggi 6 oy)
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = queryset.filter(created_at__gte=six_months_ago).annotate(
            month=TruncMonth('created_at')
        ).values('month', 'severity').annotate(count=Count('id')).order_by('month')
        
        month_names = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
        monthly_trend = {}
        for item in monthly_data:
            if item['month']:
                month_name = month_names[item['month'].month - 1]
                if month_name not in monthly_trend:
                    monthly_trend[month_name] = {'month': month_name, 'critical': 0, 'major': 0, 'minor': 0, 'info': 0}
                monthly_trend[month_name][item['severity']] = item['count']
        
        stats = {
            'total': queryset.count(),
            'resolved': queryset.filter(is_resolved=True).count(),
            'unresolved': queryset.filter(is_resolved=False).count(),
            'by_severity': by_severity,
            'by_type': by_type,
            'monthly_trend': list(monthly_trend.values()),
        }
        
        return Response(stats)
    
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


@api_view(['POST'])
@permission_classes([])
def check_spelling(request):
    """
    Check spelling in text using AI model.
    
    Request body:
    {
        "text": "Tekshiriladigan matn",
        "language": "uz_latin",
        "use_ai": true  # Optional: use AI for checking
    }
    """
    try:
        text = request.data.get('text', '')
        language = request.data.get('language', 'auto')
        use_ai = request.data.get('use_ai', True)
        
        if not text:
            return Response(
                {'error': 'Matn kiritilmadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(text) > 10000:
            return Response(
                {'error': 'Matn juda uzun (maksimum 10000 belgi)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        

        error_list = []

        # Try AI-based checking first
        if use_ai:
            try:
                import ollama
                import json
                import re

                client = ollama.Client(host='http://localhost:11434')

                prompt = f"""Sen o'zbek tili imlo tekshiruvchisi mutaxassisissan. Quyidagi matnni tekshir va FAQAT xatolarni top.

Matn: "{text}"

Har bir topilgan xato uchun quyidagi formatda javob ber (JSON array):
[
  {{"word": "xato_soz", "suggestion": "togri_soz", "description": "Xato tavsifi"}}
]

Qoidalar:
1. x harfi o'rniga h bo'lishi kerak bo'lgan so'zlarni top (masalan: xozir→hozir, xech→hech, xam→ham)
2. Tutuq belgisi (') tushib qolgan so'zlarni top (masalan: yoq→yo'q, boladi→bo'ladi, kop→ko'p)
3. Noto'g'ri yozilgan so'zlarni top (masalan: qaley→qanday, blan→bilan)
4. Grammatik xatolarni top

Agar xato topilmasa, bo'sh array qaytar: []
FAQAT JSON formatda javob ber, boshqa hech narsa yozma."""

                response = client.chat(
                    model='llama3.1',
                    messages=[{'role': 'user', 'content': prompt}]
                )

                ai_response = response['message']['content'].strip()

                # Parse JSON from response
                json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if json_match:
                    try:
                        ai_errors = json.loads(json_match.group())

                        for i, err in enumerate(ai_errors):
                            if isinstance(err, dict) and 'word' in err and 'suggestion' in err:
                                # Find position of word in text
                                word = err.get('word', '')
                                pos = text.lower().find(word.lower())

                                error_list.append({
                                    'word': word,
                                    'suggestion': err.get('suggestion', ''),
                                    'error_type': 'ai_detected',
                                    'position': pos if pos >= 0 else i * 10,
                                    'line_number': 1,
                                    'context': text[:100] + ('...' if len(text) > 100 else ''),
                                    'language': language,
                                    'description': err.get('description', f"'{word}' → '{err.get('suggestion', '')}'"),
                                })
                    except json.JSONDecodeError:
                        pass

            except Exception as e:
                # If AI fails, fall back to dictionary-based checking
                print(f"AI spelling check failed: {e}, falling back to dictionary")
                use_ai = False

        # Always run fallback (dictionary-based) checking and add its errors
        from ai_engine.spelling import SpellingChecker
        checker = SpellingChecker()
        errors = checker.check_text(text, language)
        for error in errors:
            # Avoid duplicates: only add if not already in error_list
            if not any(error.word == e.get('word') and error.suggestion == e.get('suggestion') for e in error_list):
                error_list.append({
                    'word': error.word,
                    'suggestion': error.suggestion,
                    'error_type': error.error_type.value,
                    'position': error.position,
                    'line_number': error.line_number,
                    'context': error.context,
                    'language': error.language,
                    'description': error.description,
                })

        return Response({
            'errors': error_list,
            'total_errors': len(error_list),
            'language_detected': language if language != 'auto' else 'uz_latin',
            'text_length': len(text),
            'method': 'ai+dictionary' if use_ai else 'dictionary'
        })
        
    except Exception as e:
        return Response(
            {'error': f'Xatolik: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
