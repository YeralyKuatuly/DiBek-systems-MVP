from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    Company,
    Item,
    Cart,
    CartItem,
    OrderRequest,
    OneCIntegration,
)
from core.services import (
    create_business_document_from_order,
    OneCService,
)


class Command(BaseCommand):
    help = (
        'Test 1C integration by creating sample documents '
        'and exporting them'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--integration-id',
            type=int,
            help='ID of the 1C integration to test'
        )
        parser.add_argument(
            '--document-type',
            type=str,
            default='invoice',
            choices=['invoice', 'act', 'waybill', 'tax_invoice'],
            help='Type of document to create and test'
        )

    def handle(self, *args, **options):
        self.stdout.write('🧪 Starting 1C integration test...')
        # Get or create test data
        user = self._get_or_create_test_user()
        company = self._get_or_create_test_company()
        item = self._get_or_create_test_item(company)
        order = self._get_or_create_test_order(user, item)
        # Create business document
        self.stdout.write(
            f'📄 Creating {options["document_type"]} document...'
        )
        document = create_business_document_from_order(
            order, options['document_type']
        )
        self.stdout.write(f'✅ Created document: {document.document_number}')
        # Test 1C integration
        integration = self._get_integration(options['integration_id'])
        if integration:
            self._test_1c_export(document, integration)
        else:
            self.stdout.write(
                '⚠️  No 1C integration configured. Skipping export test.'
            )
        self.stdout.write('🎉 1C integration test completed!')

    def _get_or_create_test_user(self):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            bin_number='123456789012',
            defaults={
                'email': 'test@example.com',
                'password': 'testpass123'
            }
        )
        if created:
            self.stdout.write(f'👤 Created test user: {user.bin_number}')
        return user

    def _get_or_create_test_company(self):
        company, created = Company.objects.get_or_create(
            name='Test Company LLC'
        )
        if created:
            self.stdout.write(f'🏢 Created test company: {company.name}')
        return company

    def _get_or_create_test_item(self, company):
        item, created = Item.objects.get_or_create(
            title='Test Product',
            defaults={
                'price': 100.00,
                'company': company,
                'category': 'Test'
            }
        )
        if created:
            self.stdout.write(f'📦 Created test item: {item.title}')
        return item

    def _get_or_create_test_order(self, user, item):
        # Create cart and add item
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_item, _ = CartItem.objects.get_or_create(
            cart=cart,
            item=item,
            defaults={'quantity': 2}
        )
        # Create order
        order, _ = OrderRequest.objects.get_or_create(
            cart=cart,
            defaults={
                'total_amount': item.price * cart_item.quantity,
                'status': 'pending'
            }
        )
        if _:
            self.stdout.write(f'🛒 Created test order: {order.id}')
        return order

    def _get_integration(self, integration_id):
        if integration_id:
            try:
                return OneCIntegration.objects.get(id=integration_id)
            except OneCIntegration.DoesNotExist:
                self.stdout.write(
                    f'❌ Integration with ID {integration_id} not found'
                )
                return None
        # Get first active integration
        return OneCIntegration.objects.filter(is_active=True).first()

    def _test_1c_export(self, document, integration):
        self.stdout.write(
            f'🔗 Testing export to 1C integration: {integration.name}'
        )
        try:
            onec_service = OneCService(integration)
            result = onec_service.export_document_to_1c(document)
            if result.get('success'):
                self.stdout.write(
                    f'✅ Export successful: {result.get("message")}'
                )
                if 'file_path' in result:
                    self.stdout.write(
                        f'📁 File saved to: {result["file_path"]}'
                    )
                if 'external_id' in result:
                    self.stdout.write(
                        f'🆔 1C External ID: {result["external_id"]}'
                    )
            else:
                self.stdout.write(
                    f'❌ Export failed: {result.get("message")}'
                )
        except Exception as e:
            self.stdout.write(f'❌ Export error: {str(e)}')
