from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
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

     # Total sales and quantity sold by product
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, SUM(od.Quantity) AS TotalUnitsSold, SUM(od.Quantity * od.UnitPrice) AS TotalSales
            FROM Products p
            JOIN OrderDetails od ON p.ProductID = od.ProductID
            GROUP BY p.ProductID, p.ProductName
            ORDER BY TotalSales DESC
            LIMIT 5
        """)
        total_sales_data = cursor.fetchall()
        insights['total_sales_data'] = [
            {'ProductID': row[0], 'ProductName': row[1], 'TotalUnitsSold': row[2], 'TotalSales': round(row[3], 2)}
            for row in total_sales_data
        ]

        # Best selling products per category
        cursor.execute("""
            SELECT p.Category, p.ProductID, p.ProductName, SUM(od.Quantity * od.UnitPrice) AS TotalSales
            FROM Products p
            JOIN OrderDetails od ON p.ProductID = od.ProductID
            GROUP BY p.Category, p.ProductID, p.ProductName
            ORDER BY p.Category, TotalSales DESC
            LIMIT 5
        """)
        best_selling_per_category = cursor.fetchall()
        insights['best_selling_per_category'] = [
            {'Category': row[0], 'ProductID': row[1], 'ProductName': row[2], 'TotalSales': round(row[3], 2)}
            for row in best_selling_per_category
        ]

        # Total sales per product category
        cursor.execute("""
            SELECT p.Category, SUM(od.Quantity * od.UnitPrice) AS TotalSales
            FROM Products p
            JOIN OrderDetails od ON p.ProductID = od.ProductID
            GROUP BY p.Category
            LIMIT 5
        """)
        total_sales_per_category = cursor.fetchall()
        insights['total_sales_per_category'] = [
            {'Category': row[0], 'TotalSales': round(row[1], 2)}
            for row in total_sales_per_category
        ]

        # Products not sold in the last month
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, p.Category
            FROM Products p
            WHERE p.ProductID NOT IN (
                SELECT od.ProductID
                FROM OrderDetails od
                JOIN Orders o ON od.OrderID = o.OrderID
                WHERE o.OrderDate >= CURDATE() - INTERVAL 1 MONTH
            )
            LIMIT 5
        """)
        products_not_sold_last_month = cursor.fetchall()
        insights['products_not_sold_last_month'] = [
            {'ProductID': row[0], 'ProductName': row[1], 'Category': row[2]}
            for row in products_not_sold_last_month
        ]

        # Customers without recent transactions (past 1 year)
        cursor.execute("""
            SELECT c.CustomerID, c.Name, c.Email
            FROM Customers c
            WHERE NOT EXISTS (
                SELECT 1
                FROM Orders o
                WHERE o.CustomerID = c.CustomerID AND o.OrderDate > CURDATE() - INTERVAL 1 YEAR
            )
            LIMIT 5
        """)
        customers_without_recent_transactions = cursor.fetchall()
        insights['customers_without_recent_transactions'] = [
            {'CustomerID': row[0], 'Name': row[1], 'Email': row[2]}
            for row in customers_without_recent_transactions
        ]

    return render(request, 'retail/index.html', {'insights': insights})

#Product Management - Create/Sell/Remove products
@login_required
def product_list(request):
    product_name = request.GET.get('ProductName', '')
    product_id = request.GET.get('ProductID', '')

    sql_query = """
        SELECT ProductID, ProductName, Category, UnitPrice, ProductDescription
        FROM Products
        WHERE (ProductName LIKE %s OR %s = '')
            AND (ProductID LIKE %s OR %s = '')
        ORDER BY ProductName
    """
   
    params = [f"%{product_name}%", product_name, f"%{product_id}%", product_id]

    with connection.cursor() as cursor:
        cursor.execute(sql_query, params)
        results = cursor.fetchall()

    products = [
        {
            'ProductID': row[0],
            'ProductName': row[1],
            'Category': row[2],
            'UnitPrice': row[3],
            'ProductDescription': row[4],
        }
        for row in results
    ]

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'retail/product_list.html', {
        'page_obj': page_obj,
        'product_name': product_name,
        'product_id': product_id
    })



@login_required
def product_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('ProductID')
        product_name = request.POST.get('ProductName')
        category = request.POST.get('Category')
        product_description = request.POST.get('ProductDescription')
        unit_price = request.POST.get('UnitPrice')
        stock_quantity = request.POST.get('StockQuantity')
        last_restocked = request.POST.get('LastRestocked')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Products (ProductID, ProductName, Category, ProductDescription, UnitPrice)
                VALUES (%s, %s, %s, %s, %s)
            """, [product_id, product_name, category, product_description, unit_price])
            cursor.execute("""
                INSERT INTO Inventory (ProductID_id, StockQuantity, LastRestocked)
                VALUES (%s, %s, %s)
            """, [product_id, stock_quantity, last_restocked])
        
        messages.success(request, 'Product successfully created!')
        return redirect('product_list')
    return render(request, 'retail/product_form.html')

@login_required
def product_detail(request, product_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ProductID, ProductName, Category, UnitPrice, ProductDescription
            FROM Products
            WHERE ProductID = %s
        """, [product_id])
        
        product = cursor.fetchone()

        if product is None:
            return HttpResponse("Product not found", status=404)
        
        product_detail = {
            'ProductID': product[0],
            'ProductName': product[1],
            'Category': product[2],
            'UnitPrice': product[3],
            'ProductDescription': product[4],
        }

        return render(request, 'retail/product_detail.html', {'product': product_detail})

@login_required
def product_delete(request, product_id):
    with connection.cursor() as cursor:
        cursor.execute("START TRANSACTION")
        cursor.execute("DELETE FROM orderdetails WHERE ProductID = %s", [product_id])
        cursor.execute("DELETE FROM Inventory WHERE ProductID = %s", [product_id])
        cursor.execute("DELETE FROM Products WHERE ProductID = %s", [product_id])
        cursor.execute("COMMIT")
    
    messages.success(request, 'Product successfully deleted!')
    return redirect('product_list')

@login_required
def product_update_price(request, product_id):
    if request.method == 'POST':
        new_price = request.POST.get('UnitPrice')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE Products
                SET UnitPrice = %s
                WHERE ProductID = %s
            """, [new_price, product_id])
        
        return redirect('product_detail', product_id=product_id)
    return render(request, 'retail/product_update_price.html', {'product_id': product_id})

@login_required
def product_update_description(request, product_id):
    if request.method == 'POST':
        new_description = request.POST.get('ProductDescription')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE Products
                SET ProductDescription = %s
                WHERE ProductID = %s
            """, [new_description, product_id])
        
        return redirect('product_detail', product_id=product_id)
    return render(request, 'retail/product_update_description.html', {'product_id': product_id})


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

#Search Filter

#Inventory Page
@login_required
def inventory_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT i.ProductID, p.ProductName, i.StockQuantity, i.LastRestocked
            FROM inventory i
            JOIN products p ON i.ProductID = p.ProductID
        """)
        results = cursor.fetchall()

    inventory = [
        {
            'ProductID': row[0],
            'ProductName': row[1],
            'StockQuantity': row[2],
            'LastRestocked': row[3]
        }
        for row in results
    ]

    paginator = Paginator(inventory, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'retail/inventory_list.html', {'page_obj': page_obj})

@login_required
def inventory_update(request, product_id):
    if request.method == 'POST':
        stock_quantity = request.POST.get('StockQuantity')
        last_restocked = request.POST.get('LastRestocked')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE inventory
                SET StockQuantity = %s, LastRestocked = %s
                WHERE ProductID = %s
            """, [stock_quantity, last_restocked, product_id])
        
        messages.success(request, 'Inventory successfully updated!')
        return redirect('inventory_list')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ProductID, StockQuantity, LastRestocked
            FROM inventory
            WHERE ProductID = %s
        """, [product_id])
        inventory = cursor.fetchone()

    if inventory is None:
        return HttpResponse('Product not found in inventory', status=404)

    inventory_detail = {
        'ProductID': inventory[0],
        'StockQuantity': inventory[1],
        'LastRestocked': inventory[2]
    }

    return render(request, 'retail/inventory_update.html', {'inventory': inventory_detail})
