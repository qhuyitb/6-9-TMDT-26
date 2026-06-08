import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from apps.products.models import Product


PHONE_ERROR_MESSAGE = 'Số điện thoại phải là số nội địa hợp lệ, ví dụ 0912345678.'
PHONE_PATTERN = r'^0[35789]\d{8}$'
PHONE_INPUT_PATTERN = r'^0[35789]\d{8}$'
PHONE_VALIDATOR = RegexValidator(regex=PHONE_INPUT_PATTERN, message=PHONE_ERROR_MESSAGE)


def normalize_phone_number(value):
    phone = re.sub(r'[^\d+]', '', str(value or '').strip())
    if not phone:
        return ''

    if phone.startswith('+'):
        phone = phone[1:]

    return phone


def validate_phone_number(value):
    phone = normalize_phone_number(value)
    if not re.fullmatch(PHONE_PATTERN, phone):
        raise ValidationError(PHONE_ERROR_MESSAGE)
    return phone


class UserManager(BaseUserManager):
    """Manager tùy chỉnh cho User model, hỗ trợ tạo user và superuser."""

    def create_user(self, email, phone, full_name, password=None, **extra_fields):
        """Tạo và lưu user thường với email, phone, full_name và password."""
        if not email:
            raise ValueError('Email là bắt buộc')
        if not phone:
            raise ValueError('Số điện thoại là bắt buộc')

        email = self.normalize_email(email)
        phone = validate_phone_number(phone)
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

    password = models.CharField(max_length=255, db_column='password_hash')
    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=150, unique=True)
    phone = models.CharField(max_length=10, unique=True, validators=[PHONE_VALIDATOR])
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

    def save(self, *args, **kwargs):
        self.phone = validate_phone_number(self.phone)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Cart(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_CHECKED_OUT = 'checked_out'
    STATUS_ABANDONED = 'abandoned'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CHECKED_OUT, 'Checked out'),
        (STATUS_ABANDONED, 'Abandoned'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'
        constraints = [
            models.CheckConstraint(
                check=Q(user__isnull=False) | Q(session_id__isnull=False),
                name='cart_user_or_session_required'
            )
        ]

    def __str__(self):
        return f'Cart - {self.user.email}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'


class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    receiver_name = models.CharField(max_length=150)
    receiver_phone = models.CharField(max_length=10, validators=[PHONE_VALIDATOR])
    line1 = models.CharField(max_length=255)
    ward = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_addresses'

    def save(self, *args, **kwargs):
        self.receiver_phone = validate_phone_number(self.receiver_phone)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.email} - {self.line1}'


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists', null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wishlists'
        constraints = [
            models.CheckConstraint(
                check=Q(user__isnull=False) | Q(session_id__isnull=False),
                name='wishlist_user_or_session_required'
            )
        ]

    def __str__(self):
        return f'Wishlist - {self.user.email if self.user else self.session_id}'


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlist_items'
        unique_together = ('wishlist', 'product')

    def __str__(self):
        return f'{self.product.name} - wishlist'

