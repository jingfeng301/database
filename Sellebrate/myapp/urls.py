from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('products/', views.product_list, name = 'product_list'),
    path('orders/', views.order_list, name = 'order_list'),
    # path('orders/<str:order_id>/', views.order_status, name = 'order_detail'),
]