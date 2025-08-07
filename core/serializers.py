from rest_framework import serializers
from .models import User, Cart, CartItem, OrderRequest, Company, Item, Payment


class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('bin_number', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated):
        return User.objects.create_user(**validated)

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ('item', 'quantity')

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True)
    class Meta:
        model = Cart
        fields = ('items',)

class OrderRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderRequest
        fields = '__all__'
        read_only_fields = ('status', 'created_at', 'total_amount', 'cart')

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
