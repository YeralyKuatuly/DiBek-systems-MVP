"""
1C Integration Configuration Settings

This file contains configuration options for integrating with 1C:Enterprise.
You can override these settings in your main settings.py file.
"""

# 1C Integration Default Settings
ONEC_DEFAULT_SETTINGS = {
    # Web Service Configuration
    'WEBSERVICE_TIMEOUT': 30,  # seconds
    'WEBSERVICE_RETRY_ATTEMPTS': 3,
    'WEBSERVICE_RETRY_DELAY': 5,  # seconds

    # File Export Configuration
    'DEFAULT_EXPORT_PATH': 'exports/',
    'DEFAULT_IMPORT_PATH': 'imports/',
    'DEFAULT_FILE_FORMAT': 'json',

    # Document Settings
    'DEFAULT_VAT_RATE': 12.0,  # Kazakhstan VAT rate
    'DOCUMENT_NUMBER_PREFIX': {
        'invoice': 'INV',
        'act': 'ACT',
        'waybill': 'WAY',
        'tax_invoice': 'TAX',
        'tax_report': 'REP',
    },

    # Synchronization Settings
    'AUTO_SYNC_ENABLED': False,
    'SYNC_INTERVAL': 60,  # minutes
    'BATCH_SIZE': 100,  # documents per batch

    # Logging Settings
    'LOG_SYNC_ACTIVITY': True,
    'LOG_LEVEL': 'INFO',
    'MAX_LOG_ENTRIES': 1000,
}

# 1C Web Service Endpoints (examples)
ONEC_WEBSERVICE_ENDPOINTS = {
    'production': {
        'wsdl_url': 'http://your-1c-server/ws/Exchange.1cws?wsdl',
        'username': 'your_username',
        'password': 'your_password',
        'timeout': 60,
    },
    'staging': {
        'wsdl_url': 'http://staging-1c-server/ws/Exchange.1cws?wsdl',
        'username': 'staging_user',
        'password': 'staging_password',
        'timeout': 30,
    },
    'development': {
        'wsdl_url': 'http://dev-1c-server/ws/Exchange.1cws?wsdl',
        'username': 'dev_user',
        'password': 'dev_password',
        'timeout': 15,
    },
}

# Document Type Mappings
ONEC_DOCUMENT_MAPPINGS = {
    'invoice': {
        'onec_type': 'Счет',
        'template': 'invoice_template.xml',
        'required_fields': ['number', 'date', 'seller', 'buyer', 'items'],
    },
    'act': {
        'onec_type': 'АктВыполненныхРабот',
        'template': 'act_template.xml',
        'required_fields': ['number', 'date', 'seller', 'buyer', 'services'],
    },
    'waybill': {
        'onec_type': 'ТоварнаяНакладная',
        'template': 'waybill_template.xml',
        'required_fields': ['number', 'date', 'seller', 'buyer', 'goods'],
    },
    'tax_invoice': {
        'onec_type': 'СчетФактура',
        'template': 'tax_invoice_template.xml',
        'required_fields': ['number', 'date', 'seller', 'buyer', 'items', 'vat'],
    },
}

# Error Messages (Russian)
ONEC_ERROR_MESSAGES = {
    'connection_failed': 'Ошибка подключения к 1C серверу',
    'authentication_failed': 'Ошибка аутентификации в 1C',
    'document_not_found': 'Документ не найден в 1C',
    'export_failed': 'Ошибка экспорта документа в 1C',
    'import_failed': 'Ошибка импорта данных из 1C',
    'invalid_format': 'Неверный формат данных для 1C',
    'timeout': 'Превышено время ожидания ответа от 1C',
    'server_error': 'Внутренняя ошибка сервера 1C',
}

# Success Messages (Russian)
ONEC_SUCCESS_MESSAGES = {
    'document_exported': 'Документ успешно экспортирован в 1C',
    'document_imported': 'Документ успешно импортирован из 1C',
    'sync_completed': 'Синхронизация с 1C завершена успешно',
    'connection_established': 'Соединение с 1C установлено',
}
