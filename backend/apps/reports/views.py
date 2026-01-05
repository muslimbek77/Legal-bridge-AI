"""
Views for Reports app.
"""

from rest_framework import viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from django.core.files.base import ContentFile

from apps.contracts.models import Contract
from apps.analysis.models import AnalysisResult
from .models import Report
from .serializers import ReportSerializer, GenerateReportSerializer
from .generators import PDFReportGenerator


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reports."""

    def initialize_request(self, request, *args, **kwargs):
        # Remap 'format' query param to 'report_format' before DRF processes it
        query_params = request.GET.copy()
        if 'format' in query_params and query_params['format']:
            query_params['report_format'] = query_params['format']
            del query_params['format']
            request.GET = query_params
        return super().initialize_request(request, *args, **kwargs)
    
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['contract', 'report_type', 'report_format']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'contract__title']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Report.objects.select_related('contract', 'analysis', 'generated_by')

        # Support legacy 'format' param by mapping it to 'report_format'
        request = self.request
        params = request.query_params.copy()
        if 'format' in params and params['format']:
            params = params.copy()
            params['report_format'] = params['format']
            # Remove 'format' to avoid DRF reserved param issues
            del params['format']
            # Replace request.query_params with the new params for filtering
            request._request.GET = params

        if not user.is_admin:
            queryset = queryset.filter(contract__uploaded_by=user)

        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new report."""
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract_id = serializer.validated_data['contract_id']
        report_type = serializer.validated_data['report_type']
        format_type = serializer.validated_data['report_format']
        
        # Get contract
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Shartnoma topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get latest analysis
        analysis = contract.analyses.filter(
            status=AnalysisResult.AnalysisStatus.COMPLETED
        ).order_by('-created_at').first()
        
        if not analysis:
            return Response(
                {'error': 'Shartnoma hali tahlil qilinmagan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate report
        if format_type == 'pdf':
            generator = PDFReportGenerator()
            
            if report_type == 'analysis':
                file_buffer = generator.generate_analysis_report(analysis)
            elif report_type == 'compliance':
                file_buffer = generator.generate_compliance_report(contract, analysis)
            elif report_type == 'risk':
                file_buffer = generator.generate_risk_report(contract, analysis)
            else:
                file_buffer = generator.generate_analysis_report(analysis)
            
            # Create report record
            report = Report.objects.create(
                contract=contract,
                analysis=analysis,
                report_type=report_type,
                report_format=format_type,
                title=f"{contract.title or contract.original_filename} - {report_type.upper()} hisoboti",
                generated_by=request.user
            )
            
            # Save file
            filename = f"report_{report.id}.pdf"
            report.file.save(filename, ContentFile(file_buffer.read()))
            report.file_size = report.file.size
            report.save()
            
            serializer = ReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(
            {'error': 'Bu format hozircha qo\'llab-quvvatlanmaydi'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report file."""
        report = self.get_object()
        
        if not report.file:
            return Response(
                {'error': 'Fayl topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determine file extension and content type
        ext = report.report_format or 'pdf'
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'html': 'text/html',
            'json': 'application/json',
        }
        content_type = content_types.get(ext, 'application/octet-stream')
        response = FileResponse(
            report.file.open('rb'),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{report.title}.{ext}"'
        return response
