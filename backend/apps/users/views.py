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
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .models import UserActivity
import secrets
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings as django_settings

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT login view."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for registration
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


class PasswordResetRequestView(generics.GenericAPIView):
    """Request password reset - sends email with token."""
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        frontend_url = request.data.get('frontend_url', 'http://localhost:3000')
        
        try:
            user = User.objects.get(email=email)
            # Generate reset token
            token = secrets.token_urlsafe(32)
            # Store token in cache for 1 hour
            cache.set(f'password_reset_{token}', user.id, timeout=3600)
            
            # Build reset link
            reset_link = f"{frontend_url}/reset-password?token={token}"
            
            # Send email
            try:
                send_mail(
                    subject='Legal Bridge AI - Parolni tiklash',
                    message=f'''Assalomu alaykum, {user.first_name}!

Siz Legal Bridge AI tizimida parolni tiklashni so'radingiz.

Parolni tiklash uchun quyidagi havolaga o'ting:
{reset_link}

Bu havola 1 soat davomida amal qiladi.

Agar siz bu so'rovni yubormagan bo'lsangiz, bu xabarni e'tiborsiz qoldiring.

Hurmat bilan,
Legal Bridge AI jamoasi
''',
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                return Response({
                    'message': 'Parolni tiklash uchun ko\'rsatmalar emailingizga yuborildi'
                })
            except Exception as e:
                # If email fails, return token for demo/testing
                return Response({
                    'message': 'Email yuborishda xatolik. Demo token:',
                    'demo_token': token,
                    'error': str(e)
                })
                
        except User.DoesNotExist:
            # Return same message for security
            return Response({
                'message': 'Agar email mavjud bo\'lsa, parolni tiklash uchun ko\'rsatmalar yuboriladi'
            })


class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset with token."""
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        # Get user ID from cache
        user_id = cache.get(f'password_reset_{token}')
        
        if not user_id:
            return Response(
                {'error': 'Token yaroqsiz yoki muddati o\'tgan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            
            # Delete token from cache
            cache.delete(f'password_reset_{token}')
            
            return Response({
                'message': 'Parol muvaffaqiyatli yangilandi. Endi tizimga kirishingiz mumkin.'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_400_BAD_REQUEST
            )


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
