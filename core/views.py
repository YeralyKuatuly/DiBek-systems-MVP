from rest_framework.response import Response
from .models import Company, Item, Cart, CartItem, OrderRequest, Payment
from .services import validate_bin
from .serializers import (
    SignUpSerializer, CompanySerializer, ItemSerializer,
    CartSerializer, OrderRequestSerializer,
    PaymentSerializer
)
from rest_framework import (
    generics, status, viewsets, permissions,
    mixins, decorators, response
)


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
        user = serializer.save()

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
        qty     = int(request.data.get('quantity', 1))
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
        total = sum(ci.item.price * ci.quantity for ci in cart.cartitem_set.all())
        serializer.save(cart=cart, total_amount=total)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    # hook into create() to call your KaspiClient/HalykClient…
