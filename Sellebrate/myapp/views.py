from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .forms import *
import pandas as pd
import tabulate

#This will make the user be required to login before they can view the data
def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        hashed_password = make_password(password)

        # Check if the username already exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", [username])
            if cursor.fetchone()[0] > 0:
                return render(request, 'retail/register.html', {'error': 'Username already exists'})

            # Attempt to insert the new user
            try:
                cursor.execute("INSERT INTO users (Username, Password) VALUES (%s, %s)", [username, hashed_password])
                return redirect('login')
            except IntegrityError:
                return render(request, 'retail/register.html', {'error': 'Username already exists'})
    
    # If the request method is GET or other, render the registration form
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
            messages.error(request, 'Invalid login details')
            return render(request, 'retail/login.html')
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

        # Customer retention rate
        cursor.execute("""
        WITH FirstOrders AS (
            SELECT CustomerID, MIN(OrderDate) AS FirstOrderDate
            FROM Orders
            GROUP BY CustomerID
        ),
        ReturningCustomers AS (
            SELECT fo.CustomerID, COUNT(o.OrderID) AS OrderCount
            FROM FirstOrders fo
            JOIN Orders o ON fo.CustomerID = o.CustomerID AND o.OrderDate > fo.FirstOrderDate
            GROUP BY fo.CustomerID
        )
        SELECT
            COUNT(CASE WHEN OrderCount > 1 THEN 1 END) * 1.0 / COUNT(*) AS RetentionRate
        FROM ReturningCustomers
        """)
        customer_retention_rate = cursor.fetchone()[0]
        insights['customer_retention_rate'] = round(customer_retention_rate, 2) if customer_retention_rate is not None else 0.00
        
        # Average order value
        cursor.execute("SELECT AVG(TotalAmount) FROM Orders")
        average_order_value = cursor.fetchone()[0]
        insights['average_order_value'] = round(average_order_value, 2) if average_order_value is not None else 0.00
        
        # Average number of products per order
        cursor.execute("SELECT AVG(Quantity) FROM OrderDetails")
        average_products_per_order = cursor.fetchone()[0]
        insights['average_products_per_order'] = round(average_products_per_order, 2) if average_products_per_order is not None else 0.00
        
        # MRR
        cursor.execute("""
        SELECT
            SUM(TotalAmount) / (DATEDIFF(MAX(OrderDate), MIN(OrderDate)) / 30) AS MRR
        FROM Orders
        """)
        mrr = cursor.fetchone()[0]
        insights['mrr'] = round(mrr, 2) if mrr is not None else 0.00
                
        # LTV
        cursor.execute("""
        SELECT
            AVG(TotalAmount) * AVG(DateDiff) AS LTV
        FROM (
            SELECT TotalAmount, 1.0 / DATEDIFF(CURDATE(), OrderDate) AS DateDiff
            FROM Orders
        ) AS subquery
        """)
        ltv = cursor.fetchone()[0]
        insights['ltv'] = round(ltv, 2) if ltv is not None else 0.00
        
        # ARPU
        cursor.execute("""
        SELECT
            SUM(TotalAmount) / COUNT(DISTINCT CustomerID) AS ARPU
        FROM Orders
        """)
        arpu = cursor.fetchone()[0]
        insights['arpu'] = round(arpu, 2) if arpu is not None else 0.00
        
        # Average order value
        cursor.execute("""
            SELECT AVG(TotalAmount) AS AOV
            FROM orders
        """)
        aov = cursor.fetchone()[0]
        insights['aov'] = round(aov, 2) if aov is not None else 0.00

        # Customer retention rate
        cursor.execute("""
            SELECT COUNT(DISTINCT CustomerID) AS RetainedCustomers
            FROM orders
            WHERE OrderDate >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        """)
        retained_customers = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT CustomerID) AS TotalCustomers
            FROM orders
            WHERE OrderDate < DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        """)
        total_customers = cursor.fetchone()[0]

        if total_customers > 0:
            crr = (retained_customers / total_customers) * 100
        else:
            crr = 0.0

        insights['crr'] = round(crr, 2)

        # Average products per order
        cursor.execute("""
            SELECT AVG(Quantity) AS AvgProductsPerOrder
            FROM OrderDetails
        """)
        avg_products_per_order = cursor.fetchone()[0]
        insights['avg_products_per_order'] = round(avg_products_per_order, 2) if avg_products_per_order is not None else 0.00

        # Conversion rate
        cursor.execute("""
            SELECT COUNT(DISTINCT CustomerID) AS CustomersWithOrders
            FROM orders
        """)
        customers_with_orders = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT CustomerID) AS TotalCustomers
            FROM customers
        """)
        total_customers = cursor.fetchone()[0]

        if total_customers > 0:
            conversion_rate = (customers_with_orders / total_customers) * 100
        else:
            conversion_rate = 0.0

        insights['conversion_rate'] = round(conversion_rate, 2)

        # Average order frequency
        cursor.execute("""
            SELECT AVG(OrderFrequency) AS AvgOrderFrequency
            FROM (
                SELECT CustomerID, COUNT(OrderID) AS OrderFrequency
                FROM orders
                GROUP BY CustomerID
            ) AS CustomerOrders
        """)
        avg_order_frequency = cursor.fetchone()[0]
        insights['avg_order_frequency'] = round(avg_order_frequency, 2) if avg_order_frequency is not None else 0.00

        # Inventory turnover ratio
        cursor.execute("""
            SELECT SUM(TotalQuantitySold) / AVG(StockQuantity) AS InventoryTurnoverRatio
            FROM (
                SELECT SUM(Quantity) AS TotalQuantitySold
                FROM OrderDetails
            ) AS TotalSales,
            (
                SELECT AVG(StockQuantity) AS StockQuantity
                FROM inventory
            ) AS AverageStock
        """)
        inventory_turnover_ratio = cursor.fetchone()[0]
        insights['inventory_turnover_ratio'] = round(inventory_turnover_ratio, 2) if inventory_turnover_ratio is not None else 0.00

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

        # Products with low stock
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, i.StockQuantity
            FROM Products p
            JOIN Inventory i ON p.ProductID = i.ProductID
            WHERE i.StockQuantity < 10
            ORDER BY i.StockQuantity
            LIMIT 5
        """)
        low_stock_products = cursor.fetchall()
        insights['low_stock_products'] = [
            {'ProductID': row[0], 'ProductName': row[1], 'StockQuantity': row[2]}
            for row in low_stock_products
        ]

        # Products with no stock
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, i.StockQuantity
            FROM Products p
            JOIN Inventory i ON p.ProductID = i.ProductID
            WHERE i.StockQuantity = 0
            LIMIT 5
        """)
        no_stock_products = cursor.fetchall()
        insights['no_stock_products'] = [
            {'ProductID': row[0], 'ProductName': row[1]}
            for row in no_stock_products
        ]

        # Customers with the highest total amount spent
        cursor.execute("""
            SELECT o.CustomerID, c.Name, c.Email, SUM(o.TotalAmount) AS TotalAmountSpent
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            GROUP BY o.CustomerID, c.Name, c.Email
            ORDER BY TotalAmountSpent DESC
            LIMIT 5
        """)
        customers_highest_total_amount_spent = cursor.fetchall()
        insights['customers_highest_total_amount_spent'] = [
            {'CustomerID': row[0], 'Name': row[1], 'Email': row[2], 'TotalAmountSpent': round(row[3], 2)}
            for row in customers_highest_total_amount_spent
        ]

        # Customers with the highest number of orders
        cursor.execute("""
            SELECT o.CustomerID, c.Name, c.Email, COUNT(o.OrderID) AS TotalOrders
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            GROUP BY o.CustomerID, c.Name, c.Email
            ORDER BY TotalOrders DESC
            LIMIT 5
        """)
        customers_highest_total_orders = cursor.fetchall()
        insights['customers_highest_total_orders'] = [
            {'CustomerID': row[0], 'Name': row[1], 'Email': row[2], 'TotalOrders': row[3]}
            for row in customers_highest_total_orders
        ]

        # Customers with the highest average order amount
        cursor.execute("""
            SELECT o.CustomerID, c.Name, c.Email, AVG(o.TotalAmount) AS AverageOrderAmount
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            GROUP BY o.CustomerID, c.Name, c.Email
            ORDER BY AverageOrderAmount DESC
            LIMIT 5
        """)
        customers_highest_average_order_amount = cursor.fetchall()
        insights['customers_highest_average_order_amount'] = [
            {'CustomerID': row[0], 'Name': row[1], 'Email': row[2], 'AverageOrderAmount': round(row[3], 2)}
            for row in customers_highest_average_order_amount
        ]

        # Customers with the highest number of products purchased
        cursor.execute("""
            SELECT o.CustomerID, c.Name, c.Email, SUM(od.Quantity) AS TotalProductsPurchased
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            JOIN OrderDetails od ON o.OrderID = od.OrderID
            GROUP BY o.CustomerID, c.Name, c.Email
            ORDER BY TotalProductsPurchased DESC
            LIMIT 5
        """)
        customers_highest_total_products_purchased = cursor.fetchall()
        insights['customers_highest_total_products_purchased'] = [
            {'CustomerID': row[0], 'Name': row[1], 'Email': row[2], 'TotalProductsPurchased': row[3]}
            for row in customers_highest_total_products_purchased
        ]

        # Customers with the highest average number of products purchased
        cursor.execute("""
            SELECT o.CustomerID, c.Name, c.Email, AVG(od.Quantity) AS AverageProductsPurchased
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            JOIN OrderDetails od ON o.OrderID = od.OrderID
            GROUP BY o.CustomerID, c.Name, c.Email
            ORDER BY AverageProductsPurchased DESC
            LIMIT 5
        """)
        customers_highest_average_products_purchased = cursor.fetchall()
        insights['customers_highest_average_products_purchased'] = [
            {'CustomerID': row[0], 'Name': row[1], 'Email': row[2], 'AverageProductsPurchased': round(row[3], 2)}
            for row in customers_highest_average_products_purchased
        ]

        # Customers with the highest average order amount
        cursor.execute("""
            SELECT o.CustomerID, c.Name, c.Email, AVG(o.TotalAmount) AS AverageOrderAmount
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            GROUP BY o.CustomerID, c.Name, c.Email
            ORDER BY AverageOrderAmount DESC
            LIMIT 5
        """)
        customers_highest_average_order_amount = cursor.fetchall()
        insights['customers_highest_average_order_amount'] = [
            {'CustomerID': row[0], 'Name': row[1], 'Email': row[2], 'AverageOrderAmount': round(row[3], 2)}
            for row in customers_highest_average_order_amount
        ]

        # Average sales per day
        cursor.execute("""
            SELECT
                DATE(OrderDate) AS SaleDate,
                AVG(TotalAmount) AS AverageSales
            FROM Orders
            GROUP BY DATE(OrderDate)
            ORDER BY SaleDate DESC
            LIMIT 30
        """)
        average_sales_per_day = cursor.fetchall()
        insights['average_sales_per_day'] = [
            {'SaleDate': row[0], 'AverageSales': round(row[1], 2)}
            for row in average_sales_per_day
        ]

        # Top N products sold together
        cursor.execute("""
            SELECT
                od1.ProductID AS ProductID1,
                od2.ProductID AS ProductID2,
                COUNT(*) AS TimesSoldTogether
            FROM OrderDetails od1
            JOIN OrderDetails od2 ON od1.OrderID = od2.OrderID AND od1.ProductID < od2.ProductID
            GROUP BY ProductID1, ProductID2
            ORDER BY TimesSoldTogether DESC
            LIMIT 10
        """)
        top_products_sold_together = cursor.fetchall()
        insights['top_products_sold_together'] = [
            {'ProductID1': row[0], 'ProductID2': row[1], 'TimesSoldTogether': row[2]}
            for row in top_products_sold_together
        ]

        # Average customer order value
        cursor.execute("""
        SELECT
            CustomerID,
            AVG(TotalAmount) AS AverageOrderValue
        FROM Orders
        GROUP BY CustomerID
        ORDER BY AverageOrderValue DESC
        LIMIT 10
        """)
        average_customer_order_value = cursor.fetchall()
        insights['average_customer_order_value'] = [
            {'CustomerID': row[0], 'AverageOrderValue': round(row[1], 2)}
            for row in average_customer_order_value
        ]

        # Monthly sales trend for each product
        cursor.execute("""
        SELECT
            p.ProductName,
            YEAR(o.OrderDate) AS Year,
            MONTH(o.OrderDate) AS Month,
            SUM(od.Quantity * od.UnitPrice) AS TotalSales
        FROM OrderDetails od
        JOIN Orders o ON od.OrderID = o.OrderID
        JOIN Products p ON od.ProductID = p.ProductID
        GROUP BY p.ProductName, YEAR(o.OrderDate), MONTH(o.OrderDate)
        ORDER BY Year DESC, Month DESC, TotalSales DESC
        LIMIT 5
        """)
        monthly_sales_trend = cursor.fetchall()
        insights['monthly_sales_trend'] = [
            {'ProductName': row[0], 'Year': row[1], 'Month': row[2], 'TotalSales': round(row[3], 2)}
            for row in monthly_sales_trend
        ]
        
        # Revenue contribution by top customers
        cursor.execute("""
        SELECT
            c.CustomerID,
            c.Name,
            SUM(o.TotalAmount) AS TotalSpent,
            SUM(o.TotalAmount) * 1.0 / (SELECT SUM(TotalAmount) FROM Orders) AS Contribution
        FROM Orders o
        JOIN Customers c ON o.CustomerID = c.CustomerID
        GROUP BY c.CustomerID, c.Name
        ORDER BY TotalSpent DESC
        LIMIT 10
        """)
        revenue_contribution_top_customers = cursor.fetchall()
        insights['revenue_contribution_top_customers'] = [
            {'CustomerID': row[0], 'Name': row[1], 'TotalSpent': round(row[2], 2), 'Contribution': round(row[3], 2)}
            for row in revenue_contribution_top_customers
        ]

        # Stock turnover rate
        cursor.execute("""
        SELECT
            p.ProductID,
            p.ProductName,
            SUM(od.Quantity) AS TotalSold,
            i.StockQuantity,
            (SUM(od.Quantity) / NULLIF(i.StockQuantity, 0)) AS StockTurnoverRate
        FROM OrderDetails od
        JOIN Products p ON od.ProductID = p.ProductID
        JOIN Inventory i ON p.ProductID = i.ProductID
        GROUP BY p.ProductID, p.ProductName, i.StockQuantity
        HAVING StockTurnoverRate IS NOT NULL
        ORDER BY StockTurnoverRate DESC
        LIMIT 10
        """)
        stock_turnover_rate = cursor.fetchall()
        insights['stock_turnover_rate'] = [
            {'ProductID': row[0], 'ProductName': row[1], 'TotalSold': row[2], 'StockQuantity': row[3], 'StockTurnoverRate': round(row[4], 2)}
            for row in stock_turnover_rate
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
                INSERT INTO Inventory (ProductID, StockQuantity, LastRestocked)
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
        new_description = request.POST.get('Description')

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
            SELECT o.OrderID, o.CustomerID, c.Name, o.OrderDate, o.TotalAmount, o.ShippingAddress, o.UserID
            FROM orders o
            JOIN customers c ON o.CustomerID = c.CustomerID
            LEFT JOIN users u ON o.UserID = u.UserID
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
            'UserID' : row[6],
        }
        for row in results
    ]

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'retail/order_list.html', {'page_obj': page_obj})

@login_required
def order_create(request):
    profiling_info = []
    if request.method == 'POST':
        order_id = request.POST.get('OrderID')
        customer_id = request.POST.get('CustomerID')
        order_date = request.POST.get('OrderDate')
        total_amount = request.POST.get('TotalAmount')
        shipping_address = request.POST.get('ShippingAddress')
        user_id = request.user.id
        
        with connection.cursor() as cursor:
            cursor.execute("SET profiling = 1;")

            # Check if the CustomerID exists
            cursor.execute("SELECT COUNT(*) FROM customers WHERE CustomerID = %s", [customer_id])
            customer_exists = cursor.fetchone()[0]
            
            if not customer_exists:
                messages.error(request, 'Error: Customer ID does not exist.')
                return render(request, 'retail/order_form.html')
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE OrderID = %s", [order_id])
            order_exists = cursor.fetchone()[0]
            
            if order_exists:
                messages.error(request, 'Error: Order ID already exists.')
                return render(request, 'retail/order_form.html')

            try:
                cursor.execute("START TRANSACTION")
                # Insert the new order
                cursor.execute("""
                    INSERT INTO orders (OrderID, CustomerID, OrderDate, TotalAmount, ShippingAddress, UserID)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [order_id, customer_id, order_date, total_amount, shipping_address, user_id])
                
                # Update the customer's last purchase date to the latest order date
                cursor.execute("""
                    UPDATE customers
                    SET LastPurchaseDate = (
                        SELECT MAX(OrderDate)
                        FROM orders
                        WHERE CustomerID = %s
                    )
                    WHERE CustomerID = %s
                """, [customer_id, customer_id])

                cursor.execute("COMMIT")
                messages.success(request, 'Order successfully created!')
                
                profiling_info = get_profiling_info(cursor)
                print_profiling_info(profiling_info)
            
            except Exception as e:
                cursor.execute("ROLLBACK")
                messages.error(request, f'An error occurred while creating the order: {str(e)}')
                print_profiling_info(profiling_info)
                return render(request, 'retail/order_form.html')
            
        print_profiling_info(profiling_info)
        return redirect('order_list')
    
    print_profiling_info(profiling_info)
    return render(request, 'retail/order_form.html')

@login_required
def order_detail(request, order_id):
    profiling_info = []
    with connection.cursor() as cursor:
        cursor.execute("SET profiling = 1;")
        cursor.execute("""
            SELECT o.OrderID, o.CustomerID, c.Name, o.OrderDate, o.TotalAmount, o.ShippingAddress
            FROM orders o
            JOIN customers c ON o.CustomerID = c.CustomerID
            WHERE o.OrderID = %s
        """, [order_id])
        
        order = cursor.fetchone()

        if order is None:
            return HttpResponse("Order not found", status=404)
        
        order_detail = {
            'OrderID': order[0],
            'CustomerID': order[1],
            'CustomerName': order[2],
            'OrderDate': order[3],
            'TotalAmount': order[4],
            'ShippingAddress': order[5],
        }

        cursor.execute("""
            SELECT p.ProductName, od.Quantity
            FROM orderdetails od
            JOIN products p ON od.ProductID = p.ProductID
            WHERE od.OrderID = %s
        """, [order_id])

        product_details = cursor.fetchall()

        profiling_info = get_profiling_info(cursor)
        print_profiling_info(profiling_info)

        return render(request, 'retail/order_detail.html', {'order': order_detail, 'product_details': product_details})

@login_required
def order_delete(request, order_id):
    profiling_info = []
    with connection.cursor() as cursor:
        try:
            cursor.execute("SET profiling = 1;")
            cursor.execute("START TRANSACTION")
            
            cursor.execute("SELECT CustomerID FROM orders WHERE OrderID = %s", [order_id])
            customer_id = cursor.fetchone()
            
            if not customer_id:
                messages.error(request, 'Order not found.')
                return redirect('order_list')
            
            customer_id = customer_id[0]
            
            cursor.execute("DELETE FROM transactions WHERE OrderID = %s", [order_id])
            cursor.execute("DELETE FROM orderdetails WHERE OrderID = %s", [order_id])
            cursor.execute("DELETE FROM orders WHERE OrderID = %s", [order_id])
            
            # Update the customer's last purchase date to the latest order date
            cursor.execute("""
                UPDATE customers
                SET LastPurchaseDate = (
                    SELECT MAX(OrderDate)
                    FROM orders
                    WHERE CustomerID = %s
                )
                WHERE CustomerID = %s
            """, [customer_id, customer_id])
            
            cursor.execute("""
                SELECT COUNT(*) FROM orders WHERE CustomerID = %s
            """, [customer_id])
            remaining_orders = cursor.fetchone()[0]
            
            if remaining_orders == 0:
                cursor.execute("""
                    UPDATE customers
                    SET LastPurchaseDate = NULL
                    WHERE CustomerID = %s
                """, [customer_id])
            
            cursor.execute("COMMIT")
            messages.success(request, 'Order successfully deleted!')

            profiling_info = get_profiling_info(cursor)
            print_profiling_info(profiling_info)

        except Exception as e:
            cursor.execute("ROLLBACK")
            messages.error(request, f'An error occurred while deleting the order: {str(e)}')
    
    return redirect('order_list')

@login_required
def order_update(request, order_id):
    profiling_info = []
    if request.method == 'POST':
        customer_id = request.POST.get('CustomerID')
        order_date = request.POST.get('OrderDate')
        total_amount = request.POST.get('TotalAmount')
        shipping_address = request.POST.get('ShippingAddress')

        with connection.cursor() as cursor:
            cursor.execute("SET profiling = 1;")
            cursor.execute("SELECT COUNT(*) FROM customers WHERE CustomerID = %s", [customer_id])
            customer_exists = cursor.fetchone()[0]

            if not customer_exists:
                messages.error(request, 'Error: Customer ID does not exist.')
                return render(request, 'retail/order_form.html', {'order': {
                    'CustomerID': customer_id,
                    'OrderDate': order_date,
                    'TotalAmount': total_amount,
                    'ShippingAddress': shipping_address,
                    'profiling_info': profiling_info
                }})

            try:
                cursor.execute("START TRANSACTION")

                cursor.execute("""
                    UPDATE orders
                    SET CustomerID = %s, OrderDate = %s, TotalAmount = %s, ShippingAddress = %s
                    WHERE OrderID = %s
                """, [customer_id, order_date, total_amount, shipping_address, order_id])

                # Update the customer's last purchase date to the latest order date
                cursor.execute("""
                    UPDATE customers
                    SET LastPurchaseDate = (
                        SELECT MAX(OrderDate)
                        FROM orders
                        WHERE CustomerID = %s
                    )
                    WHERE CustomerID = %s
                """, [customer_id, customer_id])

                cursor.execute("COMMIT")
                messages.success(request, 'Order successfully updated!')
                profiling_info = get_profiling_info(cursor)
                print_profiling_info(profiling_info)
                return redirect('order_list')

            except Exception as e:
                cursor.execute("ROLLBACK")
                messages.error(request, f'An error occurred while updating the order: {str(e)}')
                return render(request, 'retail/order_form.html', {'order': {
                    'CustomerID': customer_id,
                    'OrderDate': order_date,
                    'TotalAmount': total_amount,
                    'ShippingAddress': shipping_address,
                    'profiling_info': profiling_info
                }})

    with connection.cursor() as cursor:
        cursor.execute("SET profiling = 1;")
        cursor.execute("""
            SELECT OrderID, CustomerID, OrderDate, TotalAmount, ShippingAddress
            FROM orders
            WHERE OrderID = %s
        """, [order_id])
        order = cursor.fetchone()

        profiling_info = get_profiling_info(cursor)

    if order is None:
        return HttpResponse("Order not found", status=404)

    order_detail = {
        'OrderID': order[0],
        'CustomerID': order[1],
        'OrderDate': order[2],
        'TotalAmount': order[3],
        'ShippingAddress': order[4],
    }

    print_profiling_info(profiling_info)
    return render(request, 'retail/order_form.html', {'order': order_detail})

#Customer Management - View customer details/Create new customer/Update customer details/Delete customer
@login_required
def customer_list(request):
    customer_name = request.GET.get('Name', '')
    customer_id = request.GET.get('CustomerID', '')

    sql_query = """
        SELECT CustomerID, Name, Email, ContactNumber, Address, Country, LastPurchaseDate
        FROM customers
        WHERE (Name LIKE %s OR %s = '')
            AND (CustomerID LIKE %s OR %s = '')
        ORDER BY Name
    """
    
    params = [f"%{customer_name}%", customer_name, f"%{customer_id}%", customer_id]

    with connection.cursor() as cursor:
        cursor.execute(sql_query, params)
        results = cursor.fetchall()

    customers = [
        {
            'CustomerID': row[0],
            'Name': row[1],
            'Email': row[2],
            'ContactNumber': row[3],
            'Address': row[4],
            'Country': row[5],
            'LastPurchaseDate': row[6],
        }
        for row in results
    ]

    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'retail/customer_list.html', {
        'page_obj': page_obj,
        'customer_name': customer_name,
        'customer_id': customer_id
    })

@login_required
def customer_create(request):
    if request.method == 'POST':
        customer_id = request.POST.get('CustomerID')
        name = request.POST.get('Name')
        email = request.POST.get('Email')
        contact_number = request.POST.get('ContactNumber')
        address = request.POST.get('Address')
        country = request.POST.get('Country')
        last_purchase_date = request.POST.get('LastPurchaseDate')

        with connection.cursor() as cursor:
            if last_purchase_date:
                cursor.execute("""
                    INSERT INTO customers (CustomerID, Name, Email, ContactNumber, Address, Country, LastPurchaseDate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [customer_id, name, email, contact_number, address, country, last_purchase_date])
            else:
                cursor.execute("""
                    INSERT INTO customers (CustomerID, Name, Email, ContactNumber, Address, Country, LastPurchaseDate)
                    VALUES (%s, %s, %s, %s, %s, %s, NULL)
                """, [customer_id, name, email, contact_number, address, country])
        
        messages.success(request, 'Customer successfully created!')
        return redirect('customer_list')
    return render(request, 'retail/customer_form.html')

@login_required
def customer_detail(request, customer_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT CustomerID, Name, Email, ContactNumber, Address, Country, LastPurchaseDate
            FROM customers
            WHERE CustomerID = %s
        """, [customer_id])
        
        customer = cursor.fetchone()

        if customer is None:
            return HttpResponse("Customer not found", status=404)
        
        customer_detail = {
            'CustomerID': customer[0],
            'Name': customer[1],
            'Email': customer[2],
            'ContactNumber': customer[3],
            'Address': customer[4],
            'Country': customer[5],
            'LastPurchaseDate': customer[6],
        }

        return render(request, 'retail/customer_detail.html', {'customer': customer_detail})
    
@login_required
def customer_delete(request, customer_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM orders WHERE CustomerID = %s", [customer_id])
        order_count = cursor.fetchone()[0]

        if order_count > 0:
            messages.error(request, 'Cannot delete customer with existing orders.')
            return redirect('customer_list')

        cursor.execute("START TRANSACTION")
        cursor.execute("DELETE FROM customers WHERE CustomerID = %s", [customer_id])
        cursor.execute("COMMIT")
    
    messages.success(request, 'Customer successfully deleted!')
    return redirect('customer_list')

@login_required
def customer_update(request, customer_id):
    if request.method == 'POST':
        name = request.POST.get('Name')
        email = request.POST.get('Email')
        contact_number = request.POST.get('ContactNumber')
        address = request.POST.get('Address')
        country = request.POST.get('Country')
        last_purchase_date = request.POST.get('LastPurchaseDate')

        with connection.cursor() as cursor:
            if last_purchase_date:
                cursor.execute("""
                    UPDATE customers
                    SET Name = %s, Email = %s, ContactNumber = %s, Address = %s, Country = %s, LastPurchaseDate = %s
                    WHERE CustomerID = %s
                """, [name, email, contact_number, address, country, last_purchase_date, customer_id])
            else:
                cursor.execute("""
                    UPDATE customers
                    SET Name = %s, Email = %s, ContactNumber = %s, Address = %s, Country = %s
                    WHERE CustomerID = %s
                """, [name, email, contact_number, address, country, customer_id])
        
        messages.success(request, 'Customer successfully updated!')
        return redirect('customer_list')
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT CustomerID, Name, Email, ContactNumber, Address, Country, DATE_FORMAT(LastPurchaseDate, '%%Y-%%m-%%d')
                FROM customers
                WHERE CustomerID = %s
            """, [customer_id])
            
            customer = cursor.fetchone()

            if customer is None:
                return HttpResponse("Customer not found", status=404)
            
            customer_detail = {
                'CustomerID': customer[0],
                'Name': customer[1],
                'Email': customer[2],
                'ContactNumber': customer[3],
                'Address': customer[4],
                'Country': customer[5],
                'LastPurchaseDate': customer[6],
            }
        
    return render(request, 'retail/customer_form.html', {'customer': customer_detail})


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
        'LastRestocked': inventory[2].strftime('%Y-%m-%d')
    }

    return render(request, 'retail/inventory_update.html', {'inventory': inventory_detail})

@login_required
def get_low_stock_alerts(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT AlertID, ProductID, AlertDate, Message
            FROM LowStockAlerts
            WHERE Processed = FALSE
        """)
        alerts = cursor.fetchall()
    
    alerts_list = [
        {'AlertID': row[0], 'ProductID': row[1], 'AlertDate': row[2], 'Message': row[3]}
        for row in alerts
    ]

    return JsonResponse(alerts_list, safe=False)

@csrf_exempt
@login_required
def mark_alert_as_processed(request):
    alert_id = request.POST.get('alert_id')
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE LowStockAlerts
            SET Processed = TRUE
            WHERE AlertID = %s
        """, [alert_id])
    
    return JsonResponse({'status': 'success'})

def get_profiling_info(cursor):
    cursor.execute("SHOW PROFILES;")
    profiles = cursor.fetchall()
    profiling_info = []
    for profile in profiles:
        query_id = profile[0]
        query_time = profile[1]
        cursor.execute(f"SHOW PROFILE FOR QUERY {query_id};")
        profiling_info.append((query_time, cursor.fetchall()))
    return profiling_info

def print_profiling_info(profiling_info):
    pd.set_option('display.float_format', '{:.9f}'.format)
    for query_time, profile in profiling_info:
        print(f"\nProfiling info for Query executed in {query_time:.9f} seconds:\n")
        df = pd.DataFrame(profile, columns=['Stage', 'Duration'])
        print(tabulate.tabulate(df, headers='keys', tablefmt='psql'))