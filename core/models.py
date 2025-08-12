from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, bin_number, email, password=None, **extra):
        if not bin_number or not email:
            raise ValueError("BIN and email required")
        user = self.model(bin_number=bin_number,
                          email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, bin_number, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        if extra.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(bin_number, email, password, **extra)


class User(AbstractBaseUser):
    bin_number = models.CharField(max_length=12, unique=True)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'bin_number'
    REQUIRED_FIELDS = ['email']
    objects = UserManager()

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Company(models.Model):
    name = models.CharField(max_length=100)


class Item(models.Model):
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    items = models.ManyToManyField(Item, through='CartItem')


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class OrderRequest(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    order = models.ForeignKey(OrderRequest, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


class BusinessDocument(models.Model):
    """Base model for all business documents"""
    DOCUMENT_TYPES = [
        ('invoice', 'Счёт'),
        ('act', 'Акт выполненных работ'),
        ('waybill', 'Накладная'),
        ('tax_invoice', 'Счёт-фактура'),
        ('tax_report', 'Налоговая отчётность'),
    ]

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    order = models.ForeignKey(OrderRequest, on_delete=models.CASCADE)
    company_seller = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='seller_documents'
    )
    company_buyer = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='buyer_documents'
    )

    document_number = models.CharField(max_length=50, unique=True)
    document_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=12.0
    )  # Kazakhstan VAT
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, default='draft', choices=[
        ('draft', 'Черновик'),
        ('sent', 'Отправлен'),
        ('confirmed', 'Подтверждён'),
        ('paid', 'Оплачен'),
        ('cancelled', 'Отменён'),
    ])

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-document_date', '-created_at']

    def __str__(self):
        return f"{self.get_document_type_display()} #{self.document_number}"


class DocumentItem(models.Model):
    """Items within a business document"""
    document = models.ForeignKey(
        BusinessDocument, on_delete=models.CASCADE, related_name='items'
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class OneCIntegration(models.Model):
    """Configuration for 1C integration"""
    INTEGRATION_TYPES = [
        ('webservice', 'Web Service'),
        ('file_export', 'File Export/Import'),
        ('hybrid', 'Hybrid'),
    ]

    name = models.CharField(max_length=100)
    integration_type = models.CharField(
        max_length=20, choices=INTEGRATION_TYPES
    )

    # Web Service Configuration
    wsdl_url = models.URLField(blank=True, null=True)
    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=100, blank=True)

    # File Export Configuration
    export_path = models.CharField(max_length=255, blank=True)
    import_path = models.CharField(max_length=255, blank=True)
    file_format = models.CharField(max_length=20, default='xml', choices=[
        ('xml', 'XML'),
        ('json', 'JSON'),
        ('csv', 'CSV'),
    ])

    # Integration Settings
    auto_sync = models.BooleanField(default=False)
    sync_interval = models.PositiveIntegerField(
        default=60, help_text='Minutes'
    )
    last_sync = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '1C Integration'
        verbose_name_plural = '1C Integrations'

    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"


class DocumentSyncLog(models.Model):
    """Log of document synchronization with 1C"""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE)
    integration = models.ForeignKey(OneCIntegration, on_delete=models.CASCADE)

    sync_type = models.CharField(max_length=20, choices=[
        ('export', 'Export to 1C'),
        ('import', 'Import from 1C'),
        ('update', 'Update in 1C'),
    ])

    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ])

    message = models.TextField(blank=True)
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.document} - "
            f"{self.get_sync_type_display()} "
            f"({self.get_status_display()})"
        )
