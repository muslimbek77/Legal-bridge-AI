"""
Views for Users app.
"""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserActivitySerializer,
)
from .models import UserActivity

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT login view."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view."""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Change password endpoint."""
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = self.get_object()
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Parol muvaffaqiyatli o\'zgartirildi'
        })


class UserViewSet(viewsets.ModelViewSet):
    """User management viewset (admin only)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'is_active', 'organization']
    search_fields = ['email', 'first_name', 'last_name', 'organization']
    ordering_fields = ['created_at', 'email', 'last_name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        # Non-admins can only see users in their organization
        if user.organization:
            return User.objects.filter(organization=user.organization)
        return User.objects.filter(id=user.id)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user account."""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'Foydalanuvchi faollashtirildi'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account."""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'Foydalanuvchi o\'chirildi'})
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get user activity history."""
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user)[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """User activity log viewset."""
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'action']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserActivity.objects.all()
        return UserActivity.objects.filter(user=user)
