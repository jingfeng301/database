from django.contrib import admin
from .models import Customer, Inventory, OrderDetail, Order, PaymentMethod, Product, Transaction

admin.site.register(Customer)
admin.site.register(Inventory)
admin.site.register(Order)
admin.site.register(OrderDetail)
admin.site.register(PaymentMethod)
admin.site.register(Product)
admin.site.register(Transaction)

