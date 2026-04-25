from django import forms
from .models import Product, InventoryOperation


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'quantity', 'price', 'threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class InventoryOperationForm(forms.ModelForm):
    class Meta:
        model = InventoryOperation
        fields = ['product', 'operation_type', 'quantity', 'note']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'operation_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
