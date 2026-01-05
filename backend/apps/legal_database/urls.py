"""
URL configuration for Legal Database app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LawViewSet, LawArticleViewSet, LegalRuleViewSet, ContractTemplateViewSet

router = DefaultRouter()
router.register('laws', LawViewSet, basename='laws')
router.register('articles', LawArticleViewSet, basename='articles')
router.register('rules', LegalRuleViewSet, basename='rules')
router.register('templates', ContractTemplateViewSet, basename='templates')

urlpatterns = [
    path('', include(router.urls)),
]
