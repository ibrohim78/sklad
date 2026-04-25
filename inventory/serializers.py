from rest_framework import serializers
from .models import Category, Product, InventoryOperation, ProductHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(write_only=True, source='category', queryset=Category.objects.all())
    low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'category_id', 'quantity', 'price', 'threshold', 'created_at', 'updated_at', 'low_stock']

    def get_low_stock(self, obj):
        return obj.low_stock()


class InventoryOperationSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(write_only=True, source='product', queryset=Product.objects.all())
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = InventoryOperation
        fields = ['id', 'product', 'product_id', 'user', 'operation_type', 'quantity', 'note', 'created_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value


class ProductHistorySerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    user = serializers.StringRelatedField()

    class Meta:
        model = ProductHistory
        fields = ['id', 'product', 'user', 'action', 'delta', 'note', 'created_at']
