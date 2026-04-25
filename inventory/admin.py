from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Product, InventoryOperation, ProductHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'price', 'threshold', 'updated_at')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(InventoryOperation)
class InventoryOperationAdmin(admin.ModelAdmin):
    list_display = ('product', 'operation_type', 'quantity', 'user', 'created_at')
    list_filter = ('operation_type', 'product__category',)
    search_fields = ('product__name', 'user__username')


@admin.register(ProductHistory)
class ProductHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'action', 'delta', 'user', 'created_at')
    list_filter = ('action', 'product__category')
    search_fields = ('product__name', 'user__username')
