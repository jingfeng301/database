from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import *
from .forms import *

def index(request):
    return render(request, 'retail/index.html')

#Product Management - Create/Sell/Remove products
def product_list(request):
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 50)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'retail/product_list.html', {'page_obj': page_obj})

#def product_detail(request):

#def product_delete(request):

#def product_create(request):

#Order Management - View current order status
def order_list(request):
    order_list = Order.objects.all()
    paginator = Paginator(order_list, 50) 

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'retail/order_list.html', {'page_obj': page_obj})


def order_status(request,order_id):
    order = get_object_or_404(Order, OrderID=order_id)
    order_details = OrderDetail.objects.filter(OrderID = order)
    return render(request, 'retail/order_detail.html', {'order': order, 'order_details' : order_details})

#Customer - Create new user
#Login Page

#View past order as customer
#View past purchase/transaction as admin

#Update current stock and price and description of product
#Search Filter