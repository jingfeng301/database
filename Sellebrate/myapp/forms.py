from django import forms
from .models import *

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['ProductID', 'ProductName', 'Category', 'UnitPrice', 'ProductDescription']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['CustomerID', 'Name', 'Email', 'ContactNumber', 'Address', 'Country', 'LastPurchaseDate']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['OrderID', 'CustomerID', 'OrderDate', 'TotalAmount', 'ShippingAddress']

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['ProductID', 'StockQuantity', 'LastRestocked']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['OrderID', 'PaymentMethodID', 'PaymentStatus', 'PaymentDate', 'Amount']

class OrderdetailForm(forms.ModelForm):
    class Meta:
        model = OrderDetail
        fields = ['OrderID', 'ProductID', 'Quantity', 'UnitPrice']

class PaymentmethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['CustomerID', 'MethodType', 'Provider', 'ExpiryDate']