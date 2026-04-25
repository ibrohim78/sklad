from django.urls import path, include
from .views import (
    DashboardView,
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    OperationListView,
    OperationCreateView,
    LoginView,
    logout_view,
    DashboardAPIView,
    router,
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('operations/', OperationListView.as_view(), name='operation_list'),
    path('operations/new/', OperationCreateView.as_view(), name='operation_create'),
    path('api/dashboard/', DashboardAPIView.as_view(), name='api_dashboard'),
    path('api/', include(router.urls)),
]
