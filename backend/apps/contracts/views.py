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
        """Get contract statistics."""
        # For unauthenticated users, show total stats
        if request.user.is_authenticated:
            queryset = self.get_queryset()
        else:
            queryset = Contract.objects.all()
        
        stats = {
            'total': queryset.count(),
            'by_status': {},
            'by_type': {},
            'recent_uploads': list(queryset.order_by('-created_at')[:5].values(
                'id', 'title', 'status', 'created_at'
            ))
        }
        
        for status_choice in Contract.Status.choices:
            stats['by_status'][status_choice[0]] = queryset.filter(
                status=status_choice[0]
            ).count()
        
        for type_choice in Contract.ContractType.choices:
            stats['by_type'][type_choice[0]] = queryset.filter(
                contract_type=type_choice[0]
            ).count()
        
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
