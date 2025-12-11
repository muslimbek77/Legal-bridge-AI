"""
Views for Legal Database app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

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
