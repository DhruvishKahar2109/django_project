from django.db import models

# Create your models here.


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=128)

    class Meta:
        db_table = 'django_customer'

    def __str__(self):
        return self.first_name