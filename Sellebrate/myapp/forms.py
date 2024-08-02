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

class PromotionForm(forms.Form):
    ProductID = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Product ID'
    )
    PromotionName = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Promotion Name'
    )
    StartDate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Start Date'
    )
    EndDate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='End Date'
    )
    DiscountPercentage = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Discount Percentage'
    )
    
class ReviewForm(forms.Form):
    ReviewID = forms.CharField(max_length=100)
    CustomerID = forms.CharField(max_length=100)
    ProductID = forms.CharField(max_length=100)
    Rating = forms.IntegerField()
    Comment = forms.CharField(widget=forms.Textarea)
    ReviewDate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class RecommendationForm(forms.Form):
    RecommendationID = forms.CharField(max_length=100)
    CustomerID = forms.CharField(max_length=100)
    RecommendedProducts = forms.CharField(widget=forms.Textarea)  
    CreatedDate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
class SupportTicketCommentForm(forms.Form):
    Message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label='Message'
    )