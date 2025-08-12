from rest_framework.response import Response
from .models import (
    Company,
    Item,
    Cart,
    CartItem,
    OrderRequest,
    Payment,
    BusinessDocument,
    OneCIntegration,
    DocumentSyncLog,
)
from .services import validate_bin
from .serializers import (
    SignUpSerializer,
    CompanySerializer,
    ItemSerializer,
    CartSerializer,
    OrderRequestSerializer,
    PaymentSerializer,
    BusinessDocumentSerializer,
    OneCIntegrationSerializer,
    DocumentSyncLogSerializer,
)
from rest_framework import (
    generics,
    status,
    viewsets,
    permissions,
    decorators,
    response,
)
from rest_framework import serializers


class SignUpView(generics.GenericAPIView):
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        # 1) validate BIN via external gov API
        bin_number = request.data.get('bin_number')
        if not validate_bin(bin_number):
            return Response(
                {"bin_number": "Invalid or unregistered BIN."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) run serializer (will create user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 3) optionally send confirmation email here…

        return Response({"detail": "User created. Please confirm your email."},
                        status=status.HTTP_201_CREATED)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """ List & retrieve companies. """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """ List & retrieve items, with filtering via query params. """
    queryset = Item.objects.select_related('company').all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.AllowAny]


class CartViewSet(viewsets.ViewSet):
    """
    Customize:
     - GET /api/cart/         → view current user's cart
     - POST /api/cart/add/    → add item (body: {item, quantity})
     - POST /api/cart/remove/ → remove or decrement quantity
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return response.Response(CartSerializer(cart).data)

    @decorators.action(detail=False, methods=['post'])
    def add(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item_id = request.data['item']
        qty = int(request.data.get('quantity', 1))
        CartItem.objects.update_or_create(
            cart=cart, item_id=item_id,
            defaults={'quantity': qty}
        )
        return response.Response(CartSerializer(cart).data)

    @decorators.action(detail=False, methods=['post'])
    def remove(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item_id = request.data['item']
        CartItem.objects.filter(cart=cart, item_id=item_id).delete()
        return response.Response(CartSerializer(cart).data)


class OrderRequestViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD for orders.
    On create(), snapshot cart → set total_amount.
    """
    queryset = OrderRequest.objects.all()
    serializer_class = OrderRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderRequest.objects.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        total = sum(
            ci.item.price * ci.quantity for ci in cart.cartitem_set.all()
        )
        serializer.save(cart=cart, total_amount=total)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    # hook into create() to call your KaspiClient/HalykClient…


class BusinessDocumentViewSet(viewsets.ModelViewSet):
    """CRUD operations for business documents"""
    serializer_class = BusinessDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return (
            BusinessDocument.objects.filter(
                company_seller__user=self.request.user
            )
            .select_related('company_seller', 'company_buyer')
            .prefetch_related('items')
        )
    
    def perform_create(self, serializer):
        # Create document from order
        order_id = self.request.data.get('order_id')
        document_type = self.request.data.get('document_type', 'invoice')
        
        if order_id:
            from .models import OrderRequest
            try:
                order = OrderRequest.objects.get(
                    id=order_id,
                    cart__user=self.request.user
                )
                from .services import create_business_document_from_order
                document = create_business_document_from_order(
                    order, document_type
                )
                serializer.instance = document
            except OrderRequest.DoesNotExist:
                raise serializers.ValidationError("Order not found")
        else:
            serializer.save()


class OneCIntegrationViewSet(viewsets.ModelViewSet):
    """CRUD operations for 1C integration configurations"""
    queryset = OneCIntegration.objects.all()
    serializer_class = OneCIntegrationSerializer
    permission_classes = [permissions.IsAdminUser]


class DocumentSyncViewSet(viewsets.ViewSet):
    """Actions for synchronizing documents with 1C"""
    permission_classes = [permissions.IsAuthenticated]
    
    @decorators.action(detail=True, methods=['post'])
    def export_to_1c(self, request, pk=None):
        """Export a document to 1C"""
        from .models import BusinessDocument, OneCIntegration
        from .services import OneCService
        
        try:
            document = BusinessDocument.objects.get(
                id=pk,
                company_seller__user=request.user
            )
            
            # Get active 1C integration
            integration = OneCIntegration.objects.filter(
                is_active=True
            ).first()
            if not integration:
                return Response(
                    {"error": "No active 1C integration configured"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Export to 1C
            onec_service = OneCService(integration)
            result = onec_service.export_document_to_1c(document)
            
            return Response(
                {
                    "message": "Document exported successfully",
                    "result": result,
                }
            )
            
        except BusinessDocument.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Export failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @decorators.action(detail=False, methods=['post'])
    def bulk_export(self, request):
        """Export multiple documents to 1C"""
        from .models import BusinessDocument, OneCIntegration
        from .services import OneCService
        
        document_ids = request.data.get('document_ids', [])
        if not document_ids:
            return Response(
                {"error": "No document IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active 1C integration
            integration = OneCIntegration.objects.filter(
                is_active=True
            ).first()
        if not integration:
            return Response(
                {"error": "No active 1C integration configured"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Export documents
        onec_service = OneCService(integration)
        results = []
        
        for doc_id in document_ids:
            try:
                document = BusinessDocument.objects.get(
                    id=doc_id,
                    company_seller__user=request.user
                )
                result = onec_service.export_document_to_1c(document)
                results.append({
                    'document_id': doc_id,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'document_id': doc_id,
                    'success': False,
                    'error': str(e)
                })
        
        return Response(
            {
                "message": "Bulk export completed",
                "results": results,
            }
        )


class DocumentSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View synchronization logs"""
    serializer_class = DocumentSyncLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DocumentSyncLog.objects.filter(
            document__company_seller__user=self.request.user
        ).select_related('document', 'integration')
