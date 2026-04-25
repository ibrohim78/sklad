from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db.models import Count, F, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.routers import DefaultRouter

from .forms import ProductForm, InventoryOperationForm
from .filters import product_search_filter
from .models import Category, Product, InventoryOperation, ProductHistory
from .permissions import IsAdminOrWarehouse, IsEmployeeOrHigher
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    InventoryOperationSerializer,
    ProductHistorySerializer,
)
from .services import apply_inventory_operation


class WarehouseRequiredMixin(UserPassesTestMixin):
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('dashboard')
        return super().handle_no_permission()


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.all()
        operations = InventoryOperation.objects.select_related('product').all()

        context['total_products'] = products.count()
        context['total_stock'] = products.aggregate(total=Sum('quantity'))['total'] or 0
        context['total_categories'] = Category.objects.count()
        context['low_stock_products'] = products.filter(quantity__lte=F('threshold')).count()
        today = timezone.now().date()
        month_start = today.replace(day=1)

        today_incoming = operations.filter(operation_type=InventoryOperation.TYPE_IN, created_at__date=today)
        today_outgoing = operations.filter(operation_type=InventoryOperation.TYPE_OUT, created_at__date=today)
        month_incoming = operations.filter(operation_type=InventoryOperation.TYPE_IN, created_at__date__gte=month_start)
        month_outgoing = operations.filter(operation_type=InventoryOperation.TYPE_OUT, created_at__date__gte=month_start)

        context['incoming_today'] = today_incoming.count()
        context['outgoing_today'] = today_outgoing.count()
        context['incoming_today_qty'] = today_incoming.aggregate(total=Sum('quantity'))['total'] or 0
        context['outgoing_today_qty'] = today_outgoing.aggregate(total=Sum('quantity'))['total'] or 0
        context['incoming_month_qty'] = month_incoming.aggregate(total=Sum('quantity'))['total'] or 0
        context['outgoing_month_qty'] = month_outgoing.aggregate(total=Sum('quantity'))['total'] or 0
        context['category_stats'] = list(
            Category.objects
            .annotate(item_count=Count('products'))
            .order_by('-item_count')
            .values('name', 'item_count')
        )
        context['top_categories'] = context['category_stats'][:6]
        context['recent_operations'] = operations[:10]
        context['products'] = products.order_by('name')[:10]
        return context


class ProductListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/products.html'
    model = Product
    paginate_by = 20
    context_object_name = 'products'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        q = self.request.GET.get('q', '')
        return product_search_filter(queryset, q)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class ProductCreateView(LoginRequiredMixin, WarehouseRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('product_list')

    def test_func(self):
        return self.request.user.is_warehouse()


class ProductUpdateView(LoginRequiredMixin, WarehouseRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('product_list')

    def test_func(self):
        return self.request.user.is_warehouse()


class ProductDeleteView(LoginRequiredMixin, WarehouseRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')

    def test_func(self):
        return self.request.user.is_warehouse()


class OperationListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/operations.html'
    model = InventoryOperation
    paginate_by = 20
    context_object_name = 'operations'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('product', 'user')
        product_id = self.request.GET.get('product')
        op_type = self.request.GET.get('type')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if op_type in (InventoryOperation.TYPE_IN, InventoryOperation.TYPE_OUT):
            queryset = queryset.filter(operation_type=op_type)
        return queryset


class OperationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = InventoryOperation
    form_class = InventoryOperationForm
    template_name = 'inventory/operation_form.html'
    success_url = reverse_lazy('operation_list')

    def test_func(self):
        return self.request.user.is_employee()

    def form_valid(self, form):
        product = form.cleaned_data['product']
        operation_type = form.cleaned_data['operation_type']
        quantity = form.cleaned_data['quantity']
        note = form.cleaned_data['note']
        apply_inventory_operation(product=product, user=self.request.user, quantity=quantity, operation_type=operation_type, note=note)
        return super().form_valid(form)


class LoginView(DjangoLoginView):
    template_name = 'inventory/login.html'


def logout_view(request):
    logout(request)
    return redirect('login')


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminOrWarehouse]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        product = serializer.save()
        ProductHistory.objects.create(
            product=product,
            user=self.request.user,
            action=ProductHistory.ACTION_CREATE,
            delta=product.quantity,
            note='Mahsulot yaratildi via API',
        )

    def perform_update(self, serializer):
        product = serializer.save()
        ProductHistory.objects.create(
            product=product,
            user=self.request.user,
            action=ProductHistory.ACTION_UPDATE,
            delta=product.quantity,
            note='Mahsulot yangilandi via API',
        )

    def perform_destroy(self, instance):
        ProductHistory.objects.create(
            product=instance,
            user=self.request.user,
            action=ProductHistory.ACTION_DELETE,
            delta=0,
            note='Mahsulot o‘chirildi via API',
        )
        instance.delete()


class InventoryOperationViewSet(viewsets.ModelViewSet):
    queryset = InventoryOperation.objects.select_related('product', 'user').all()
    serializer_class = InventoryOperationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsEmployeeOrHigher]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        operation_type = serializer.validated_data['operation_type']
        quantity = serializer.validated_data['quantity']
        note = serializer.validated_data.get('note', '')
        operation = apply_inventory_operation(product=product, user=request.user, quantity=quantity, operation_type=operation_type, note=note)
        output = self.get_serializer(operation)
        return Response(output.data, status=status.HTTP_201_CREATED)


class ProductHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductHistory.objects.select_related('product', 'user').all()
    serializer_class = ProductHistorySerializer
    permission_classes = [IsAuthenticated]


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.all()
        operations = InventoryOperation.objects.all()
        incoming = operations.filter(operation_type=InventoryOperation.TYPE_IN).aggregate(total=Sum('quantity'))['total'] or 0
        outgoing = operations.filter(operation_type=InventoryOperation.TYPE_OUT).aggregate(total=Sum('quantity'))['total'] or 0
        low_stock = products.filter(quantity__lte=F('threshold')).count()

        return Response({
            'total_products': products.count(),
            'total_stock': products.aggregate(total=Sum('quantity'))['total'] or 0,
            'incoming_quantity': incoming,
            'outgoing_quantity': outgoing,
            'low_stock_count': low_stock,
        })


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'operations', InventoryOperationViewSet, basename='operation')
router.register(r'history', ProductHistoryViewSet, basename='history')

urlpatterns = router.urls
