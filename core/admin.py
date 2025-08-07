from django.contrib import admin
from .models import User, Company, Item, Cart, CartItem, OrderRequest, Payment

admin.site.register(User)
admin.site.register(Company)
admin.site.register(Item)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderRequest)
admin.site.register(Payment)
