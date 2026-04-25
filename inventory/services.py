from django.core.exceptions import ValidationError
from django.db import transaction
from .models import InventoryOperation, ProductHistory
from .notifications import send_low_stock_alert


def apply_inventory_operation(product, user, quantity, operation_type, note=''):
    if quantity <= 0:
        raise ValidationError('Quantity must be positive.')

    if operation_type == InventoryOperation.TYPE_OUT and product.quantity < quantity:
        raise ValidationError('Not enough stock for this operation.')

    delta = quantity if operation_type == InventoryOperation.TYPE_IN else -quantity

    with transaction.atomic():
        product.quantity = product.quantity + delta
        product.save()

        operation = InventoryOperation.objects.create(
            product=product,
            user=user,
            operation_type=operation_type,
            quantity=quantity,
            note=note,
        )

        ProductHistory.objects.create(
            product=product,
            user=user,
            action=ProductHistory.ACTION_OPERATION,
            delta=delta,
            note=note,
        )

    if product.low_stock():
        send_low_stock_alert(product)

    return operation
