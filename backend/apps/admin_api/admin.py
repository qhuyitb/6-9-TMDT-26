from django.contrib import admin
from .models import Order, OrderItem, Review, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('id',)
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'rating', 'is_visible', 'review_date')
    list_filter = ('is_visible', 'rating')
    search_fields = ('product__name', 'user__email')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'payment_method', 'amount', 'status', 'paid_at')
    list_filter = ('payment_method', 'status')
    search_fields = ('transaction_ref',)
