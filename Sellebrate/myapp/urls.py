from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('dashboard/', views.index, name='index'),
    path('orders/', views.order_list, name='order_list'),
    # path('orders/<str:order_id>/', views.order_status, name='order_status'),
    # path('orders/add/', views.order_create, name='order_create'),
    # path('orders/<str:order_id>/edit/', views.order_update, name='order_update'),
    # path('orders/<str:order_id>/delete/', views.order_delete, name='order_delete'),
    path('products/', views.product_list, name='product_list'),
    # path('products/add/', views.product_create, name='product_create'),
    # path('products/<str:product_id>/edit/', views.product_update, name='product_update'),
    # path('products/<str:product_id>/delete/', views.product_delete, name='product_delete'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
]
