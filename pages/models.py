from django.db import models
from backend.models import Product
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


# Create your models here.

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)

        customer = self.model(email=email, **extra_fields)
        customer.set_password(password)
        customer.save(using=self._db)
        return customer


class Customer(AbstractBaseUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True,blank=True, null=True)
    phone = models.CharField(max_length=20,blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    pincode = models.IntegerField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'django_customer'

    objects = CustomerManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='cart')
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'django_cart'

    def __str__(self):
        return f"Cart==- {self.customer}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product',
            )
        ]
        db_table = 'django_cart_item'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"



class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("cod","Cash on Delivery"),
        ("online","Online Payment"),
    ]

    order_number = models.CharField(max_length=30,unique=True,editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,related_name='orders')

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(blank=True, null=True,max_length=20)

    address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True,max_length=100)
    state = models.TextField(blank=True, null=True,max_length=100)
    pincode = models.IntegerField(blank=True, null=True,max_length=10)
    country = models.TextField(max_length=100,default='India')
    landmark = models.TextField(max_length=255,blank=True, null=True)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    delivery = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2,default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_part = timezone.localdate().strftime("%Y%m%d")
            last_order = Order.objects.order_by('-id').first()

            if last_order:
                next_number = last_order.id + 1
            else:
                next_number = 1
            self.order_number = (
                f"MS-{date_part}-{next_number:05d}"
            )
            super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

    class Meta:
        db_table = 'django_order'

        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    class Meta:
        db_table = 'django_order_item'