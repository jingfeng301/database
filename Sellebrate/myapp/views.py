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
