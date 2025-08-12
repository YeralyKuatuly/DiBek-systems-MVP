from rest_framework import serializers
from .models import (
    User,
    Cart,
    CartItem,
    OrderRequest,
    Company,
    Item,
    Payment,
    DocumentItem,
    BusinessDocument,
    OneCIntegration,
    DocumentSyncLog,
)


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


class DocumentItemSerializer(serializers.ModelSerializer):
    item_title = serializers.CharField(source='item.title', read_only=True)

    class Meta:
        model = DocumentItem
        fields = (
            'id',
            'item',
            'item_title',
            'quantity',
            'unit_price',
            'total_price',
        )


class BusinessDocumentSerializer(serializers.ModelSerializer):
    items = DocumentItemSerializer(many=True, read_only=True)
    document_type_display = serializers.CharField(
        source='get_document_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    company_seller_name = serializers.CharField(
        source='company_seller.name', read_only=True
    )
    company_buyer_name = serializers.CharField(
        source='company_buyer.name', read_only=True
    )

    class Meta:
        model = BusinessDocument
        fields = '__all__'
        read_only_fields = (
            'document_number',
            'document_date',
            'created_at',
            'updated_at',
        )


class OneCIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneCIntegration
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }


class DocumentSyncLogSerializer(serializers.ModelSerializer):
    document_number = serializers.CharField(
        source='document.document_number', read_only=True
    )
    integration_name = serializers.CharField(
        source='integration.name', read_only=True
    )

    class Meta:
        model = DocumentSyncLog
        fields = '__all__'
        read_only_fields = ('created_at',)
