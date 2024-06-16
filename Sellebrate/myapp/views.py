from django.shortcuts import render, get_object_or_404
from django.db import connection
from django.core.paginator import Paginator
from .models import *
from .forms import *

def index(request):
    return render(request, 'retail/index.html')

#Product Management - Create/Sell/Remove products
def product_list(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT ProductID, ProductName, Category, UnitPrice FROM products")
        results = cursor.fetchall()

    products = [
        {
            'ProductID': row[0],
            'ProductName': row[1],
            'Category': row[2],
            'UnitPrice': row[3]
        }
        for row in results
    ]

    paginator = Paginator(products, 50)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'retail/product_list.html', {'page_obj': page_obj})

#def product_detail(request):

#def product_delete(request):

#def product_create(request):

#Order Management - View current order status
def order_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.OrderID, o.CustomerID, c.Name, o.OrderDate, o.TotalAmount, o.ShippingAddress
            FROM orders o
            JOIN customers c ON o.CustomerID = c.CustomerID
        """)
        results = cursor.fetchall()
    
    orders = [
        {
            'OrderID': row[0],
            'CustomerID': row[1],
            'CustomerName': row[2],
            'OrderDate': row[3],
            'TotalAmount': row[4],
            'ShippingAddress': row[5],
        }
        for row in results
    ]

    paginator = Paginator(orders, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'retail/order_list.html', {'page_obj': page_obj})


# def order_status(request, order_id):
#     with connection.cursor() as cursor:
#         # Fetch order details
#         cursor.execute("""
#             SELECT OrderID, CustomerID, OrderDate, TotalAmount, ShippingAddress 
#             FROM orders 
#             WHERE OrderID = %s
#         """, [order_id])
#         order = cursor.fetchone()

#         if order is None:
#             raise Http404("Order does not exist")

#         order_data = {
#             'OrderID': order[0],
#             'CustomerID': order[1],
#             'OrderDate': order[2],
#             'TotalAmount': order[3],
#             'ShippingAddress': order[4]
#         }

#         cursor.execute("""
#             SELECT OrderDetailID, OrderID, ProductID, Quantity, UnitPrice 
#             FROM orderdetails 
#             WHERE OrderID = %s
#         """, [order_id])
#         order_details = cursor.fetchall()

#     order_details_data = [
#         {
#             'OrderDetailID': detail[0],
#             'OrderID': detail[1],
#             'ProductID': detail[2],
#             'Quantity': detail[3],
#             'UnitPrice': detail[4],
#         }
#         for detail in order_details
#     ]

#     return render(request, 'retail/order_detail.html', {'order': order_data, 'order_details': order_details_data})

#Customer - Create new user
#Login Page

#View past order as customer
#View past purchase/transaction as admin

#Update current stock and price and description of product
#Search Filter