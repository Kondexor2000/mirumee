from django import forms
from .models import Product, Store

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'url', 'category']

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['title']