from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

class Store(models.Model):
    title = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.ForeignKey(Store, on_delete=models.CASCADE)
    price = models.FloatField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    url = models.CharField(max_length=100)