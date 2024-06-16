from django.shortcuts import render
from .models import *
from .forms import *

def index(request):
    return render(request, 'retail/index.html')

def product_list(request):
    products = Product.objects.all()
    return render(request, 'retail/product_list.html', {'products' : products})