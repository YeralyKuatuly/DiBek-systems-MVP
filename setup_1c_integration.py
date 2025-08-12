#!/usr/bin/env python
"""
1C Integration Setup Script for DiBek MVP

This script helps you configure 1C integration for your business documents.
Choose from different integration types based on your needs.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import OneCIntegration
from django.contrib.auth import get_user_model

User = get_user_model()


def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🔧 DiBek MVP - 1C Integration Setup")
    print("=" * 60)
    print()


def print_integration_options():
    """Print available integration options"""
    print("📋 Available 1C Integration Options:")
    print()
    print("1. 📁 File Export (Recommended for testing)")
    print("   - Documents exported as JSON/XML files")
    print("   - No 1C server required")
    print("   - Manual import into 1C")
    print("   - Perfect for testing and small businesses")
    print()
    print("2. 🌐 Web Service (Production)")
    print("   - Real-time integration with 1C server")
    print("   - Requires 1C:Enterprise server")
    print("   - Automatic document synchronization")
    print("   - Best for production environments")
    print()
    print("3. 🔄 Hybrid (Advanced)")
    print("   - Combines file export and web service")
    print("   - Fallback to file export if web service fails")
    print("   - Most flexible option")
    print()


def setup_file_export():
    """Setup file export integration"""
    print("📁 Setting up File Export Integration...")
    print()

    # Get export path
    default_export_path = "exports"
    export_path = input(f"Export directory path (default: {default_export_path}): ").strip()
    if not export_path:
        export_path = default_export_path

    # Get file format
    print("\nAvailable file formats:")
    print("1. JSON (recommended for testing)")
    print("2. XML (standard for 1C)")
    print("3. CSV (simple format)")

    format_choice = input("Choose format (1-3, default: 1): ").strip()
    format_map = {"1": "json", "2": "xml", "3": "csv"}
    file_format = format_map.get(format_choice, "json")

    # Create integration
    integration = OneCIntegration.objects.create(
        name="File Export Integration",
        integration_type="file_export",
        export_path=export_path,
        file_format=file_format,
        is_active=True
    )

    print(f"\n✅ File Export Integration created!")
    print(f"   ID: {integration.id}")
    print(f"   Export Path: {export_path}")
    print(f"   File Format: {file_format.upper()}")

    return integration


def setup_web_service():
    """Setup web service integration"""
    print("🌐 Setting up Web Service Integration...")
    print()
    print("⚠️  This requires a running 1C:Enterprise server with web services enabled.")
    print()

    # Get WSDL URL
    wsdl_url = input("1C Web Service WSDL URL: ").strip()
    if not wsdl_url:
        print("❌ WSDL URL is required for web service integration")
        return None

    # Get credentials
    username = input("1C Username: ").strip()
    password = input("1C Password: ").strip()

    if not username or not password:
        print("❌ Username and password are required")
        return None

    # Create integration
    integration = OneCIntegration.objects.create(
        name="1C Web Service Integration",
        integration_type="webservice",
        wsdl_url=wsdl_url,
        username=username,
        password=password,
        is_active=True
    )

    print(f"\n✅ Web Service Integration created!")
    print(f"   ID: {integration.id}")
    print(f"   WSDL URL: {wsdl_url}")
    print(f"   Username: {username}")

    return integration


def setup_hybrid():
    """Setup hybrid integration"""
    print("🔄 Setting up Hybrid Integration...")
    print()

    # Setup web service part
    print("First, let's configure the web service part:")
    ws_integration = setup_web_service()
    if not ws_integration:
        return None

    # Setup file export part
    print("\nNow, let's configure the file export fallback:")
    fe_integration = setup_file_export()

    # Create hybrid integration
    integration = OneCIntegration.objects.create(
        name="Hybrid 1C Integration",
        integration_type="hybrid",
        wsdl_url=ws_integration.wsdl_url,
        username=ws_integration.username,
        password=ws_integration.password,
        export_path=fe_integration.export_path,
        file_format=fe_integration.file_format,
        is_active=True
    )

    # Deactivate individual integrations
    ws_integration.is_active = False
    ws_integration.save()
    fe_integration.is_active = False
    fe_integration.save()

    print(f"\n✅ Hybrid Integration created!")
    print(f"   ID: {integration.id}")
    print(f"   Primary: Web Service")
    print(f"   Fallback: File Export")

    return integration


def test_integration(integration):
    """Test the created integration"""
    print(f"\n🧪 Testing Integration...")

    try:
        from core.services import OneCService
        from core.models import BusinessDocument

        # Get a test document
        test_doc = BusinessDocument.objects.first()
        if not test_doc:
            print("⚠️  No test documents found. Create some documents first.")
            return

        # Test the integration
        service = OneCService(integration)
        result = service.export_document_to_1c(test_doc)

        if result.get('success'):
            print("✅ Integration test successful!")
            if 'file_path' in result:
                print(f"   File saved to: {result['file_path']}")
            if 'external_id' in result:
                print(f"   1C External ID: {result['external_id']}")
        else:
            print("❌ Integration test failed!")
            print(f"   Error: {result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")


def show_usage_examples():
    """Show usage examples"""
    print("\n📚 Usage Examples:")
    print("=" * 40)
    print()

    print("1. Create a business document:")
    print("   POST /api/documents/")
    print("   {")
    print('     "order_id": 1,')
    print('     "document_type": "invoice"')
    print("   }")
    print()

    print("2. Export document to 1C:")
    print("   POST /api/document-sync/1/export_to_1c/")
    print()

    print("3. Bulk export multiple documents:")
    print("   POST /api/document-sync/bulk_export/")
    print("   {")
    print('     "document_ids": [1, 2, 3]')
    print("   }")
    print()

    print("4. View sync logs:")
    print("   GET /api/sync-logs/")
    print()

    print("5. Test with management command:")
    print("   python manage.py test_1c_integration --document-type invoice")
    print()


def main():
    """Main setup function"""
    print_header()
    print_integration_options()

    # Check if integrations already exist
    existing_integrations = OneCIntegration.objects.filter(is_active=True)
    if existing_integrations.exists():
        print("⚠️  Active integrations found:")
        for integration in existing_integrations:
            print(f"   - {integration.name} (ID: {integration.id})")
        print()

        choice = input("Do you want to create a new integration? (y/N): ").strip().lower()
        if choice != 'y':
            print("Setup cancelled.")
            return

    # Choose integration type
    print("Choose integration type:")
    choice = input("1. File Export | 2. Web Service | 3. Hybrid (1-3): ").strip()

    integration = None

    if choice == "1":
        integration = setup_file_export()
    elif choice == "2":
        integration = setup_web_service()
    elif choice == "3":
        integration = setup_hybrid()
    else:
        print("❌ Invalid choice. Setup cancelled.")
        return

    if integration:
        # Test the integration
        test_choice = input("\nDo you want to test the integration? (Y/n): ").strip().lower()
        if test_choice != 'n':
            test_integration(integration)

        # Show usage examples
        show_usage_examples()

        print("\n🎉 1C Integration setup completed!")
        print(f"Integration ID: {integration.id}")
        print("You can now create and export business documents to 1C.")


if __name__ == "__main__":
    main()
