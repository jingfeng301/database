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
    ReviewID = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Review ID'
    )
    CustomerID = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Customer ID'
    )
    ProductID = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Product ID'
    )

    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ]
    
    Rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Rating'
    )
    
    Comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label='Comment'
    )
    ReviewDate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Reviewed Date'
    )

class RecommendationForm(forms.Form):
    CustomerID = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Customer ID'
    )
    RecommendedProducts = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        label='Recommended Products'
    )
    CreatedDate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Created Date'
    )
    
class SupportTicketCommentForm(forms.Form):
    Message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label='Message'
    )

class ReviewFilterForm(forms.Form):
    rating = forms.ChoiceField(
        choices=[('', 'All')] + [(i, i) for i in range(1, 6)],
        required=False
    )
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))