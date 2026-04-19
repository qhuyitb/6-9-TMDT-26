from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer


class RegisterView(generics.CreateAPIView):
    """
    API đăng ký tài khoản mới.
    Cho phép tất cả mọi người truy cập, không cần xác thực.
    POST /api/auth/register/
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Tạo tài khoản mới và trả về thông báo thành công."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Đăng ký thành công',
            'email': user.email
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API đăng nhập tài khoản.
    Trả về access_token và refresh_token nếu đăng nhập thành công.
    POST /api/auth/login/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Xác thực thông tin đăng nhập và trả về JWT token."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Đăng nhập thành công',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
            }
        }, status=status.HTTP_200_OK)