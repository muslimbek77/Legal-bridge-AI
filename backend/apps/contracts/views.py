"""
Views for Contracts app.
"""

from django.db import models as db_models
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Contract, ContractSection, ContractClause, ContractVersion, ContractComment
from .serializers import (
    ContractListSerializer,
    ContractDetailSerializer,
    ContractUploadSerializer,
    ContractUpdateSerializer,
    ContractStatusSerializer,
    ContractSectionSerializer,
    ContractCommentSerializer,
    ContractVersionSerializer,
)


class ContractViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing contracts.
    """
    queryset = Contract.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'contract_type', 'language', 'uploaded_by', 'assigned_to']
    search_fields = ['title', 'contract_number', 'party_a', 'party_b', 'extracted_text']
    ordering_fields = ['created_at', 'contract_date', 'title', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContractListSerializer
        elif self.action == 'create':
            return ContractUploadSerializer
        elif self.action in ['update', 'partial_update']:
            return ContractUpdateSerializer
        elif self.action == 'change_status':
            return ContractStatusSerializer
        return ContractDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Contract.objects.select_related('uploaded_by', 'assigned_to')
        
        # Filter based on user role
        if not user.is_admin:
            # Users can see contracts they uploaded or are assigned to
            queryset = queryset.filter(
                db_models.Q(uploaded_by=user) | db_models.Q(assigned_to=user)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change contract status."""
        contract = self.get_object()
        serializer = ContractStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract.status = serializer.validated_data['status']
        if 'notes' in serializer.validated_data:
            contract.notes = serializer.validated_data['notes']
        contract.save()
        
        return Response({
            'message': 'Holat muvaffaqiyatli o\'zgartirildi',
            'status': contract.get_status_display()
        })
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger contract analysis."""
        contract = self.get_object()
        
        if contract.status == Contract.Status.PROCESSING:
            return Response(
                {'error': 'Shartnoma allaqachon tahlil qilinmoqda'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to processing
        contract.status = Contract.Status.PROCESSING
        contract.save()
        
        # Trigger async analysis task
        from apps.analysis.tasks import analyze_contract_task
        analyze_contract_task.delay(str(contract.id))
        
        return Response({
            'message': 'Tahlil boshlandi',
            'contract_id': str(contract.id)
        })
    
    @action(detail=True, methods=['get'])
    def sections(self, request, pk=None):
        """Get contract sections."""
        contract = self.get_object()
        sections = contract.sections.all()
        serializer = ContractSectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get contract versions."""
        contract = self.get_object()
        versions = contract.versions.all()
        serializer = ContractVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_version(self, request, pk=None):
        """Add new version of contract."""
        contract = self.get_object()
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'Fayl yuklanmadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        last_version = contract.versions.order_by('-version_number').first()
        new_version_number = (last_version.version_number + 1) if last_version else 1
        
        version = ContractVersion.objects.create(
            contract=contract,
            version_number=new_version_number,
            file=request.FILES['file'],
            changes_description=request.data.get('changes_description', ''),
            created_by=request.user
        )
        
        serializer = ContractVersionSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Get or add comments."""
        contract = self.get_object()
        
        if request.method == 'GET':
            comments = contract.comments.select_related('user', 'resolved_by')
            serializer = ContractCommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = ContractCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(contract=contract, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='comments/(?P<comment_id>[^/.]+)/resolve')
    def resolve_comment(self, request, pk=None, comment_id=None):
        """Resolve a comment."""
        contract = self.get_object()
        
        try:
            comment = contract.comments.get(id=comment_id)
        except ContractComment.DoesNotExist:
            return Response(
                {'error': 'Izoh topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        comment.is_resolved = True
        comment.resolved_by = request.user
        comment.resolved_at = timezone.now()
        comment.save()
        
        serializer = ContractCommentSerializer(comment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def stats(self, request):
        """Get contract statistics for dashboard."""
        from apps.analysis.models import AnalysisResult, ComplianceIssue
        from django.db.models import Avg, Count
        from django.db.models.functions import TruncMonth
        from datetime import datetime, timedelta
        
        # Foydalanuvchi faqat o'z shartnomalarini ko'radi (admin bo'lmasa)
        if request.user.is_authenticated:
            user = request.user
            if hasattr(user, 'is_admin') and user.is_admin:
                queryset = Contract.objects.all()
            else:
                queryset = Contract.objects.filter(
                    db_models.Q(uploaded_by=user) | db_models.Q(assigned_to=user)
                )
        else:
            queryset = Contract.objects.none()
        
        # Asosiy statistika
        total = queryset.count()
        
        # Status bo'yicha
        by_status = {}
        for status_choice in Contract.Status.choices:
            by_status[status_choice[0]] = queryset.filter(status=status_choice[0]).count()
        
        # Tur bo'yicha (pie chart uchun)
        by_type = []
        type_labels = dict(Contract.ContractType.choices)
        for type_choice in Contract.ContractType.choices:
            count = queryset.filter(contract_type=type_choice[0]).count()
            if count > 0:
                by_type.append({
                    'name': type_labels[type_choice[0]],
                    'value': count,
                    'type': type_choice[0]
                })
        
        # O'rtacha risk ball va compliance
        analyses = AnalysisResult.objects.filter(contract__in=queryset, status='completed')
        avg_risk = analyses.aggregate(avg=Avg('overall_score'))['avg'] or 0
        
        # Kritik muammolar soni
        critical_issues = ComplianceIssue.objects.filter(
            analysis__contract__in=queryset,
            severity='critical',
            is_resolved=False
        ).count()
        
        # Risk taqsimoti (pie chart uchun)
        risk_distribution = [
            {'name': 'Past (0-25)', 'value': analyses.filter(overall_score__lte=25).count(), 'color': '#10B981'},
            {'name': "O'rta (25-50)", 'value': analyses.filter(overall_score__gt=25, overall_score__lte=50).count(), 'color': '#F59E0B'},
            {'name': 'Yuqori (50-75)', 'value': analyses.filter(overall_score__gt=50, overall_score__lte=75).count(), 'color': '#F97316'},
            {'name': 'Kritik (75-100)', 'value': analyses.filter(overall_score__gt=75).count(), 'color': '#EF4444'},
        ]
        
        # Oylik tahlillar (so'nggi 6 oy)
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = queryset.filter(created_at__gte=six_months_ago).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        month_names = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
        monthly_analysis = []
        for item in monthly_data:
            if item['month']:
                monthly_analysis.append({
                    'month': month_names[item['month'].month - 1],
                    'count': item['count']
                })
        
        # So'nggi shartnomalar (risk_score bilan)
        recent_contracts_qs = queryset.order_by('-created_at')[:5]
        recent_contracts = []
        for contract in recent_contracts_qs:
            latest_analysis = contract.analyses.filter(status='completed').order_by('-created_at').first()
            recent_contracts.append({
                'id': str(contract.id),
                'title': contract.title,
                'status': contract.status,
                'contract_type': contract.contract_type,
                'created_at': contract.created_at,
                'risk_score': latest_analysis.overall_score if latest_analysis else None,
                'counterparty': contract.party_b or contract.party_a or None,
            })
        
        # Muvofiqlik darajasi (o'rtacha compliance_score)
        if analyses.exists():
            avg_compliance = analyses.aggregate(avg=Avg('compliance_score'))['avg'] or 0
            compliance_rate = round(avg_compliance)
        else:
            compliance_rate = 0
        
        stats = {
            'total': total,
            'by_status': by_status,
            'by_type': by_type,
            'average_risk_score': round(avg_risk),
            'critical_issues': critical_issues,
            'compliance_rate': compliance_rate,
            'risk_distribution': risk_distribution,
            'monthly_analysis': monthly_analysis,
            'recent_contracts': recent_contracts,
        }
        
        return Response(stats)


class ContractSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for contract sections."""
    queryset = ContractSection.objects.all()
    serializer_class = ContractSectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'section_type', 'is_compliant', 'risk_level']


class ContractCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for contract comments."""
    queryset = ContractComment.objects.all()
    serializer_class = ContractCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'user', 'is_resolved']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
