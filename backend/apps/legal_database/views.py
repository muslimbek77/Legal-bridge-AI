"""
Views for Legal Database app.
"""

import io
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.http import FileResponse, HttpResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

from .models import Law, LawChapter, LawArticle, LegalRule, ContractTemplate
from .serializers import (
    LawListSerializer,
    LawDetailSerializer,
    LawChapterSerializer,
    LawArticleSerializer,
    LegalRuleSerializer,
    ContractTemplateSerializer,
    SearchQuerySerializer,
)


class LawViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing laws."""
    
    queryset = Law.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['law_type', 'status']
    search_fields = ['name', 'name_ru', 'short_name', 'description']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LawListSerializer
        return LawDetailSerializer
    
    @action(detail=True, methods=['get'])
    def articles(self, request, pk=None):
        """Get all articles of a law."""
        law = self.get_object()
        articles = law.articles.all()
        serializer = LawArticleSerializer(articles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rules(self, request, pk=None):
        """Get all rules from a law."""
        law = self.get_object()
        rules = LegalRule.objects.filter(article__law=law, is_active=True)
        serializer = LegalRuleSerializer(rules, many=True)
        return Response(serializer.data)


class LawArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing law articles."""
    
    queryset = LawArticle.objects.all()
    serializer_class = LawArticleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['law', 'chapter', 'is_mandatory']
    search_fields = ['title', 'title_ru', 'content', 'content_ru', 'keywords']
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search articles by query."""
        serializer = SearchQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data['query']
        limit = serializer.validated_data.get('limit', 10)
        contract_type = serializer.validated_data.get('contract_type')
        
        # Basic text search (in production, use vector search)
        articles = LawArticle.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(content__icontains=query) |
            models.Q(keywords__contains=[query])
        )
        
        if contract_type:
            articles = articles.filter(applies_to__contains=[contract_type])
        
        articles = articles[:limit]
        serializer = LawArticleSerializer(articles, many=True)
        return Response(serializer.data)


class LegalRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing legal rules."""
    
    queryset = LegalRule.objects.filter(is_active=True)
    serializer_class = LegalRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['rule_type', 'severity']
    search_fields = ['title', 'description']
    
    @action(detail=False, methods=['get'])
    def for_contract_type(self, request):
        """Get rules applicable to a specific contract type."""
        contract_type = request.query_params.get('type')
        
        if not contract_type:
            return Response(
                {'error': 'Shartnoma turi ko\'rsatilmagan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rules = self.queryset.filter(
            applies_to_contract_types__contains=[contract_type]
        )
        serializer = self.get_serializer(rules, many=True)
        return Response(serializer.data)


class ContractTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for contract templates."""
    
    queryset = ContractTemplate.objects.filter(is_approved=True)
    serializer_class = ContractTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['contract_type']
    search_fields = ['name', 'description']

    def _generate_pdf(self, template, language='uz_latin'):
        """Generate PDF from template text with Cyrillic support."""
        buffer = io.BytesIO()
        
        # Register DejaVu fonts for Cyrillic support
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
            font_name = 'DejaVuSans'
            font_bold = 'DejaVuSans-Bold'
        except Exception:
            font_name = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Get text based on language
        if language == 'ru':
            text = template.template_text_ru or template.template_text
            title = template.name_ru or template.name
        elif language == 'uz_cyrillic':
            text = template.template_text_cyrillic or template.template_text
            title = template.name_cyrillic or template.name
        else:
            text = template.template_text
            title = template.name
        
        # Styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName=font_bold
        )
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=11,
            spaceBefore=15,
            spaceAfter=8,
            fontName=font_bold
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leading=14,
            fontName=font_name
        )
        
        # Build content
        story = []
        
        if text:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                    continue
                
                # Escape special characters for PDF
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Title detection
                if line.isupper() or '№' in line or line.startswith('SHARTNOMA') or line.startswith('ДОГОВОР'):
                    story.append(Paragraph(line, title_style))
                # Section headers
                elif line and line[0].isdigit() and '.' in line[:3] and line.split('.')[0].isdigit():
                    parts = line.split(' ', 1)
                    if len(parts) > 1 and parts[1].isupper():
                        story.append(Paragraph(line, section_style))
                    else:
                        story.append(Paragraph(line, body_style))
                else:
                    story.append(Paragraph(line, body_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download template as PDF."""
        template = self.get_object()
        language = request.query_params.get('lang', 'uz_latin')
        
        # Agar fayl mavjud bo'lsa
        if template.template_file:
            response = FileResponse(
                template.template_file.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{template.name}.pdf"'
            return response
        
        # PDF generatsiya qilish
        if template.template_text:
            try:
                pdf_buffer = self._generate_pdf(template, language)
                
                # Language suffix for filename
                lang_suffix = {
                    'uz_latin': '_lotin',
                    'uz_cyrillic': '_kirill', 
                    'ru': '_rus'
                }.get(language, '')
                
                response = HttpResponse(
                    pdf_buffer.getvalue(),
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="{template.name}{lang_suffix}.pdf"'
                return response
            except Exception as e:
                return Response(
                    {'error': f'PDF yaratishda xatolik: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {'error': 'Shablon fayli topilmadi'},
            status=status.HTTP_404_NOT_FOUND
        )
