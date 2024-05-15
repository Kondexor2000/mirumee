from django.contrib import admin
from .models import Category, Store

# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

class StoreAdmin(admin.ModelAdmin):
    list_display = ['title']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Store, StoreAdmin)