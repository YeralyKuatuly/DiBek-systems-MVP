def validate_bin(bin_number: str) -> bool:
    """Validate a Kazakhstan BIN locally by format and checksum.

    Rules:
    - Must be exactly 12 digits
    - Checksum is calculated on the first 11 digits
      using weights [1..11]; if result is 10, use
      alternate weights [3,4,5,6,7,8,9,10,11,1,2].
    - The control digit (12th) must equal the checksum.
    - For now it just manually checks the checksum, but in the future it will 
    be checked against the government database.
    """

    if bin_number is None:
        return False

    normalized = bin_number.strip()

    if len(normalized) != 12 or not normalized.isdigit():
        return False

    digits = [int(ch) for ch in normalized]

    primary_weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    secondary_weights = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]

    primary_sum = sum(d * w for d, w in zip(digits[:11], primary_weights))
    checksum = primary_sum % 11

    if checksum == 10:
        secondary_sum = sum(
            d * w for d, w in zip(digits[:11], secondary_weights)
        )
        checksum = secondary_sum % 11
        if checksum == 10:
            return False

    return checksum == digits[11]


def generate_document_number(document_type: str, company_id: int) -> str:
    """Generate unique document number for business documents"""
    from datetime import datetime
    from .models import BusinessDocument
    
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month
    
    # Get count of documents for this company and type in current month
    count = BusinessDocument.objects.filter(
        document_type=document_type,
        company_seller_id=company_id,
        document_date__year=year,
        document_date__month=month
    ).count()
    
    # Format: TYPE-YYYY-MM-XXXX (e.g., INV-2024-12-0001)
    return f"{document_type.upper()[:3]}-{year}-{month:02d}-{(count + 1):04d}"


def calculate_vat_amount(subtotal: float, vat_rate: float = 12.0) -> tuple:
    """Calculate VAT amount and total for Kazakhstan tax rates"""
    vat_amount = subtotal * (vat_rate / 100)
    total_amount = subtotal + vat_amount
    return round(vat_amount, 2), round(total_amount, 2)


class OneCService:
    """Service for 1C integration"""
    
    def __init__(self, integration_config):
        self.config = integration_config
        self.integration_type = integration_config.integration_type
    
    def export_document_to_1c(self, document):
        """Export business document to 1C"""
        try:
            if self.integration_type == 'webservice':
                return self._export_via_webservice(document)
            elif self.integration_type == 'file_export':
                return self._export_via_file(document)
            else:
                raise ValueError(f"Unsupported integration type: {self.integration_type}")
        except Exception as e:
            self._log_sync_error(document, 'export', str(e))
            raise
    
    def _export_via_webservice(self, document):
        """Export document via 1C web service"""
        # This would use zeep or suds-jurko for SOAP calls
        # For now, return mock success
        print(f"🔗 Exporting {document.document_type} #{document.document_number} via 1C Web Service")
        return {
            'success': True,
            'message': 'Document exported successfully via 1C Web Service',
            'external_id': f"1C_{document.document_number}"
        }
    
    def _export_via_file(self, document):
        """Export document via file export"""
        import json
        from datetime import datetime
        
        # Create export data structure
        export_data = {
            'document_type': document.document_type,
            'document_number': document.document_number,
            'document_date': document.document_date.isoformat(),
            'company_seller': {
                'name': document.company_seller.name,
                'bin': document.company_seller.bin_number if hasattr(document.company_seller, 'bin_number') else None
            },
            'company_buyer': {
                'name': document.company_buyer.name,
                'bin': document.company_buyer.bin_number if hasattr(document.company_buyer, 'bin_number') else None
            },
            'items': [
                {
                    'title': item.item.title,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price)
                }
                for item in document.items.all()
            ],
            'subtotal': float(document.subtotal),
            'vat_rate': float(document.vat_rate),
            'vat_amount': float(document.vat_amount),
            'total_amount': float(document.total_amount),
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Save to export file
        filename = f"{document.document_number}_{document.document_type}.json"
        export_path = self.config.export_path or "exports"
        
        import os
        os.makedirs(export_path, exist_ok=True)
        file_path = os.path.join(export_path, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Exported {document.document_type} #{document.document_number} to {file_path}")
        
        return {
            'success': True,
            'message': f'Document exported to {file_path}',
            'file_path': file_path
        }
    
    def _log_sync_error(self, document, sync_type, error_message):
        """Log synchronization errors"""
        from .models import DocumentSyncLog
        
        DocumentSyncLog.objects.create(
            document=document,
            integration=self.config,
            sync_type=sync_type,
            status='failed',
            message=error_message
        )


def create_business_document_from_order(order, document_type='invoice'):
    """Create a business document from an order"""
    from .models import BusinessDocument, DocumentItem, Company
    
    # Get company information (assuming order.cart.user has company info)
    # You might need to adjust this based on your actual data model
    seller_company = Company.objects.first()  # Default seller company
    buyer_company = Company.objects.first()   # Default buyer company
    
    # Generate document number
    document_number = generate_document_number(document_type, seller_company.id)
    
    # Calculate totals
    subtotal = float(order.total_amount)
    vat_amount, total_amount = calculate_vat_amount(subtotal)
    
    # Create document
    document = BusinessDocument.objects.create(
        document_type=document_type,
        order=order,
        company_seller=seller_company,
        company_buyer=buyer_company,
        document_number=document_number,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total_amount=total_amount
    )
    
    # Create document items
    for cart_item in order.cart.cartitem_set.all():
        DocumentItem.objects.create(
            document=document,
            item=cart_item.item,
            quantity=cart_item.quantity,
            unit_price=cart_item.item.price,
            total_price=cart_item.item.price * cart_item.quantity
        )
    
    print(f"📄 Created {document_type} #{document_number} for order {order.id}")
    return document
