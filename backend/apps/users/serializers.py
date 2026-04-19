import re
from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, error_messages={
        "min_length": "Mật khẩu phải có ít nhất 8 ký tự."
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
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Mật khẩu phải chứa ít nhất 1 chữ in hoa.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            phone=validated_data['phone'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user