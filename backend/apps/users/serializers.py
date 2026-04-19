import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer xử lý đăng ký tài khoản.
    Kiểm tra email và số điện thoại không được trùng.
    Mật khẩu phải có ít nhất 8 ký tự và 1 chữ in hoa.
    """

    password = serializers.CharField(write_only=True, min_length=8, error_messages={
        'min_length': 'Mật khẩu phải có ít nhất 8 ký tự.'
    })

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone', 'password')
        extra_kwargs = {
            'email': {
                'error_messages': {
                    'unique': 'Email này đã được đăng ký, vui lòng sử dụng email khác.'
                }
            },
            'phone': {
                'error_messages': {
                    'unique': 'Số điện thoại này đã được sử dụng.'
                }
            }
        }

    def validate_password(self, value):
        """Kiểm tra mật khẩu phải có ít nhất 1 chữ in hoa."""
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Mật khẩu phải chứa ít nhất 1 chữ in hoa.")
        return value

    def create(self, validated_data):
        """Tạo user mới với mật khẩu đã được băm."""
        user = User.objects.create_user(
            email=validated_data['email'],
            phone=validated_data['phone'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer xử lý đăng nhập.
    Kiểm tra email, mật khẩu hợp lệ và trạng thái tài khoản.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Xác thực thông tin đăng nhập.
        Từ chối nếu sai email/mật khẩu hoặc tài khoản bị khóa/chưa kích hoạt.
        """
        email = data.get('email')
        password = data.get('password')

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Email hoặc mật khẩu không chính xác.")

        if user.status == 'locked':
            raise serializers.ValidationError("Tài khoản của bạn đã bị khóa.")

        if user.status == 'inactive':
            raise serializers.ValidationError("Tài khoản chưa được kích hoạt.")

        data['user'] = user
        return data