"""
URL configuration for Analysis app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AnalysisResultViewSet, ComplianceIssueViewSet, AnalysisFeedbackViewSet

router = DefaultRouter()
router.register('results', AnalysisResultViewSet, basename='analysis-results')
router.register('issues', ComplianceIssueViewSet, basename='issues')
router.register('feedbacks', AnalysisFeedbackViewSet, basename='feedbacks')

urlpatterns = [
    path('', include(router.urls)),
]
