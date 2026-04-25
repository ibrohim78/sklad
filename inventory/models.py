from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_WAREHOUSE = 'warehouse'
    ROLE_EMPLOYEE = 'employee'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_WAREHOUSE, 'Warehouse'),
        (ROLE_EMPLOYEE, 'Employee'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)

    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def is_warehouse(self):
        return self.role in (self.ROLE_WAREHOUSE, self.ROLE_ADMIN)

    def is_employee(self):
        return self.role in (self.ROLE_EMPLOYEE, self.ROLE_WAREHOUSE, self.ROLE_ADMIN)


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    threshold = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def low_stock(self):
        return self.quantity <= self.threshold


class InventoryOperation(models.Model):
    TYPE_IN = 'in'
    TYPE_OUT = 'out'
    TYPE_CHOICES = [
        (TYPE_IN, 'Kirim'),
        (TYPE_OUT, 'Chiqim'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='operations')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='operations')
    operation_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} {self.operation_type} {self.quantity}'


class ProductHistory(models.Model):
    ACTION_CREATE = 'created'
    ACTION_UPDATE = 'updated'
    ACTION_DELETE = 'deleted'
    ACTION_OPERATION = 'operation'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Created'),
        (ACTION_UPDATE, 'Updated'),
        (ACTION_DELETE, 'Deleted'),
        (ACTION_OPERATION, 'Operation'),
    ]

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='histories')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    delta = models.IntegerField(default=0)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        product_name = self.product.name if self.product else 'O‘chirilgan mahsulot'
        return f'{product_name} {self.action} {self.delta}'
