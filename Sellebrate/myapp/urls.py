from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('dashboard/', views.index, name='index'),
    path('orders/', views.order_list, name='order_list'),
    # path('orders/<str:order_id>/', views.order_status, name='order_status'),
    path('orders/add/', views.order_create, name='order_create'),
    path('orders/<str:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_id>/edit/', views.order_update, name='order_update'),
    path('orders/<str:order_id>/delete/', views.order_delete, name='order_delete'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<str:product_id>/', views.product_detail, name='product_detail'),
    path('products/<str:product_id>/edit/price/', views.product_update_price, name='product_update_price'),
    path('products/<str:product_id>/edit/description/', views.product_update_description, name='product_update_description'),
    path('products/<str:product_id>/delete/', views.product_delete, name='product_delete'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<str:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<str:customer_id>/update/', views.customer_update, name='customer_update'),
    path('customers/<str:customer_id>/delete/', views.customer_delete, name='customer_delete'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/<str:product_id>/update/', views.inventory_update, name='inventory_update'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
]
