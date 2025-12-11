"""
Views for Reports app.
"""

from rest_framework import viewsets, status
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
    
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['contract', 'report_type', 'format']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Report.objects.select_related('contract', 'analysis', 'generated_by')
        
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
        format_type = serializer.validated_data['format']
        
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
                format=format_type,
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
        
        response = FileResponse(
            report.file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
        return response
