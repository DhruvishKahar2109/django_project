from django.db import models
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
from .fields import OrderedForeignKey

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    parent_category = OrderedForeignKey('self', on_delete=models.CASCADE, related_name='sub_categories', blank=True,
                                        null=True, after='slug')
    description = models.TextField(blank=True)
    imageName = models.CharField(max_length=255)
    image = models.CloudinaryField('image',folder='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'django_categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True,blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    imageName = models.CharField(max_length=255)
    image = models.CloudinaryField("image",folder='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self,*args,**kwargs):
        self.slug = slugify(self.name)
        super().save(*args,**kwargs)

    class Meta:
        db_table = 'django_product'

    def __str__(self):
        return self.name