from django.db import models


class Category(models.Model):
    """
    Model danh mục sản phẩm.
    Dùng để phân loại sản phẩm (laptop, điện thoại, tai nghe,...).
    Không cho phép xóa nếu danh mục đang chứa sản phẩm.
    """
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Model sản phẩm điện tử.
    Lưu thông tin chi tiết sản phẩm bao gồm giá, tồn kho và trạng thái kinh doanh.
    
    Ràng buộc nghiệp vụ:
    - Không xóa cứng nếu sản phẩm đang trong đơn hàng đang xử lý.
    - Chuyển sang inactive/discontinued thay vì xóa.
    - Giá và số lượng tồn kho không được âm.
    """
    BUSINESS_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # Không cho xóa category nếu còn sản phẩm
        related_name='products'
    )
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    description = models.TextField(null=True, blank=True)
    specifications = models.TextField(null=True, blank=True)
    business_status = models.CharField(
        max_length=20,
        choices=BUSINESS_STATUS_CHOICES,
        default='active'
    )
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """
    Model ảnh sản phẩm.
    Mỗi sản phẩm có thể có nhiều ảnh.
    Ảnh đầu tiên (sort_order=0) mặc định là ảnh chính (is_primary=True).
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_url = models.ImageField(upload_to='products/', max_length=255)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_images'
        unique_together = ('product', 'sort_order')

    def __str__(self):
        return f"{self.product.name} - image {self.sort_order}"