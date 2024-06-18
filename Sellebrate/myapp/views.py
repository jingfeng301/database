from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import *
from .forms import *

#This will make the user be required to login before they can view the data
def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

#Register a new user
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        hashed_password = make_password(password)
        
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", [username, hashed_password])
        
        return redirect('login')
    return render(request, 'retail/register.html')

#Exisiting User login
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE username = %s", [username])
            result = cursor.fetchone()
        
        if result and check_password(password, result[0]):
            request.session['username'] = username
            return redirect('index')
        else:
            return HttpResponse('Invalid login details')
    return render(request, 'retail/login.html')

def user_logout(request):
    if 'username' in request.session:
        del request.session['username']
    return redirect('index')


#Display all the summed up info for dashboard
@login_required
def index(request):
    insights = {}
    
    with connection.cursor() as cursor:
        # Total sales
        cursor.execute("SELECT SUM(TotalAmount) FROM orders")
        total_sales = cursor.fetchone()[0]
        insights['total_sales'] = round(total_sales, 2) if total_sales is not None else 0.00

        # Total number of orders
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]
        insights['total_orders'] = total_orders

        # Total number of products
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        insights['total_products'] = total_products

        # Inventory status (e.g., number of items in stock)
        cursor.execute("SELECT SUM(StockQuantity) FROM inventory")
        total_stock = cursor.fetchone()[0]
        insights['total_stock'] = total_stock if total_stock is not None else 0

    return render(request, 'retail/index.html', {'insights': insights})

#Product Management - Create/Sell/Remove products
@login_required
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

    paginator = Paginator(products, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'retail/product_list.html', {'page_obj': page_obj})

#def product_detail(request):

#def product_delete(request):

#def product_create(request):

#Order Management - View current order status
@login_required
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

    paginator = Paginator(orders, 10)
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

#Update current stock and price and description of product
#Search Filter