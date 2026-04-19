from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Manager tùy chỉnh cho User model, hỗ trợ tạo user và superuser."""

    def create_user(self, email, phone, full_name, password=None, **extra_fields):
        """Tạo và lưu user thường với email, phone, full_name và password."""
        if not email:
            raise ValueError('Email là bắt buộc')
        if not phone:
            raise ValueError('Số điện thoại là bắt buộc')

        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, full_name, password=None, **extra_fields):
        """Tạo và lưu superuser với quyền admin đầy đủ."""
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, phone, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Model người dùng tùy chỉnh.
    Dùng email để đăng nhập thay vì username.

    Ràng buộc nghiệp vụ:
    - Email và số điện thoại phải là duy nhất.
    - Không cho phép đăng nhập nếu tài khoản bị khóa hoặc chưa kích hoạt.
    """

    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('locked', 'Locked'),
        ('inactive', 'Inactive'),
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=150, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    avatar_url = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_staff = models.BooleanField(default=False)  # Bắt buộc để dùng Django admin
    last_login_at = models.DateTimeField(null=True, blank=True)  # Theo DB schema
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'full_name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email