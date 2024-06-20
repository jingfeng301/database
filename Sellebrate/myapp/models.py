from django.db import models

class Customer(models.Model):
    CustomerID = models.CharField(max_length=512, primary_key=True)
    Name = models.CharField(max_length=512, null=True, blank=True)
    Email = models.CharField(max_length=512, null=True, blank=True)
    ContactNumber = models.CharField(max_length=512, null=True, blank=True, db_column='Contact Number')
    Address = models.CharField(max_length=512, null=True, blank=True)
    Country = models.CharField(max_length=512, null=True, blank=True)
    LastPurchaseDate = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.Name or self.CustomerID

    class Meta:
        db_table = 'customers'
        verbose_name_plural = 'customers'
        ordering = ['CustomerID']

class Users(models.Model):
    UserID =  models.AutoField(primary_key=True)
    Username = models.CharField(max_length=255)
    Password = models.CharField(max_length=255)

    def __str__(self):
        return self.UserID

    class Meta:
        db_table = 'users'
        verbose_name_plural = 'users'
        ordering = ['UserID']

class Product(models.Model):
    ProductID = models.CharField(max_length=512, primary_key=True)
    ProductName = models.CharField(max_length=512, null=True, blank=True)
    Category = models.CharField(max_length=512, null=True, blank=True)
    UnitPrice = models.FloatField(null=True, blank=True)
    ProductDescription = models.CharField(max_length=512, null=True, blank=True)

    def __str__(self):
        return self.ProductName or self.ProductID

    class Meta:
        db_table = 'products'
        verbose_name_plural = 'products'
        ordering = ['ProductID']

class Inventory(models.Model):
    ProductID = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='ProductID')
    StockQuantity = models.IntegerField(null=True, blank=True)
    LastRestocked = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.ProductID} - {self.StockQuantity}"

    class Meta:
        db_table = 'inventory'
        verbose_name_plural = 'inventory'
        ordering = ['ProductID']

class Order(models.Model):
    OrderID = models.CharField(max_length=512, primary_key=True)
    CustomerID = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='CustomerID', null=True, blank=True)
    OrderDate = models.DateField(null=True, blank=True)
    TotalAmount = models.FloatField(null=True, blank=True)
    ShippingAddress = models.CharField(max_length=512, null=True, blank=True)
    UserID = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserID', null=True, blank=True )

    def __str__(self):
        return self.OrderID

    class Meta:
        db_table = 'orders'
        verbose_name_plural = 'orders'
        ordering = ['OrderID']

class OrderDetail(models.Model):
    OrderDetailID = models.AutoField(primary_key=True)
    OrderID = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='OrderID', null=True, blank=True)
    ProductID = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='ProductID', null=True, blank=True)
    Quantity = models.IntegerField(null=True, blank=True)
    UnitPrice = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.OrderID} - {self.ProductID}"

    class Meta:
        db_table = 'orderdetails'
        verbose_name_plural = 'orderdetails'
        ordering = ['OrderDetailID']

class PaymentMethod(models.Model):
    PaymentMethodID = models.AutoField(primary_key=True)
    CustomerID = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='CustomerID', null=True, blank=True)
    MethodType = models.CharField(max_length=512, null=True, blank=True)
    Provider = models.CharField(max_length=512, null=True, blank=True)
    CardNo = models.BinaryField(null=True, blank=True)
    ExpiryDate = models.DateField(null=True, blank=True)
    CVV = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return f"{self.CustomerID} - {self.MethodType}"

    class Meta:
        db_table = 'paymentmethods'
        verbose_name_plural = 'paymentmethods'
        ordering = ['PaymentMethodID']

class Transaction(models.Model):
    TransactionID = models.AutoField(primary_key=True)
    OrderID = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='OrderID', null=True, blank=True)
    PaymentMethodID = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, db_column='PaymentMethodID', null=True, blank=True)
    PaymentStatus = models.CharField(max_length=512, null=True, blank=True)
    PaymentDate = models.DateField(null=True, blank=True)
    Amount = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.OrderID} - {self.Amount}"

    class Meta:
        db_table = 'transactions'
        verbose_name_plural = 'transactions'
        ordering = ['TransactionID']
