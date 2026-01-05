"""
URL configuration for Contracts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ContractViewSet, ContractSectionViewSet, ContractCommentViewSet

router = DefaultRouter()
router.register('', ContractViewSet, basename='contracts')
router.register('sections', ContractSectionViewSet, basename='sections')
router.register('comments', ContractCommentViewSet, basename='comments')

urlpatterns = [
    path('', include(router.urls)),
]
