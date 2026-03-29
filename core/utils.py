from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import ExchangeRate, SystemSetting

class CurrencyConverter:
    """Utility for currency conversion"""
    
    @staticmethod
    def get_latest_rate(from_currency_code, to_currency_code='DA'):
        """Get the latest exchange rate"""
        try:
            rate = ExchangeRate.objects.filter(
                from_currency__code=from_currency_code,
                to_currency__code=to_currency_code,
                effective_date__lte=timezone.now().date()
            ).first()
            return rate.rate if rate else None
        except ExchangeRate.DoesNotExist:
            return None
    
    @staticmethod
    def convert(amount, from_currency_code, to_currency_code='DA', rate=None):
        """Convert amount from one currency to another"""
        if from_currency_code == to_currency_code:
            return amount
        
        if rate is None:
            rate = CurrencyConverter.get_latest_rate(from_currency_code, to_currency_code)
        
        if rate is None:
            raise ValueError(f"Exchange rate not found for {from_currency_code} to {to_currency_code}")
        
        return amount * rate

class TaxCalculator:
    """Utility for tax calculations following Algerian rules"""
    
    @staticmethod
    def get_tva_rate():
        """Get current TVA rate from settings"""
        try:
            setting = SystemSetting.objects.get(key='tva_rate')
            return setting.get_value()
        except SystemSetting.DoesNotExist:
            return Decimal(str(settings.DEFAULT_TVA_RATE))
    
    @staticmethod
    def get_tariff_rate():
        """Get current import tariff rate"""
        try:
            setting = SystemSetting.objects.get(key='import_tariff_rate')
            return setting.get_value()
        except SystemSetting.DoesNotExist:
            return Decimal(str(settings.DEFAULT_TARIFF_RATE))
    
    @staticmethod
    def calculate_import_duty(cif_value, tariff_rate=None):
        """Calculate import duty based on CIF value"""
        if tariff_rate is None:
            tariff_rate = TaxCalculator.get_tariff_rate()
        
        return cif_value * (tariff_rate / 100)
    
    @staticmethod
    def calculate_tva(cif_value, import_duty, tva_rate=None):
        """Calculate TVA on (CIF + Import Duty)"""
        if tva_rate is None:
            tva_rate = TaxCalculator.get_tva_rate()
        
        taxable_base = cif_value + import_duty
        return taxable_base * (tva_rate / 100)
    
    @staticmethod
    def calculate_subtotal_ht(total_ttc, tva_rate=None):
        """Calculate subtotal HT from total TTC"""
        if tva_rate is None:
            tva_rate = TaxCalculator.get_tva_rate()
        
        return total_ttc / (1 + (tva_rate / 100))

class NumberFormatter:
    """Utility for formatting numbers in Algerian context"""
    
    @staticmethod
    def format_currency(amount, currency_code='DA'):
        """Format amount as currency"""
        if amount is None:
            return "0,00 DA"
        
        # Format with thousand separators
        formatted = f"{amount:,.2f}"
        return f"{formatted} {currency_code}"
    
    @staticmethod
    def format_percentage(percentage):
        """Format percentage"""
        if percentage is None:
            return "0,00%"
        
        return f"{percentage:,.2f}%"

def get_setting_value(key, default=None):
    """Get system setting value by key"""
    try:
        setting = SystemSetting.objects.get(key=key)
        return setting.get_value()
    except SystemSetting.DoesNotExist:
        return default

def check_user_permission(user, permission_type, model_name=None):
    """Check if user has specific permission based on role"""
    if not hasattr(user, 'userprofile'):
        return False
    
    profile = user.userprofile
    
    # Manager has all permissions
    if profile.is_manager:
        return True
    
    # Define permission matrix
    permissions = {
        'trader': {
            'view': ['sales', 'customers', 'inventory', 'commission'],
            'add': ['sales', 'customers'],
            'change': ['sales', 'customers'],
            'delete': []
        },
        'finance': {
            'view': ['all'],
            'add': ['suppliers', 'purchases', 'payments', 'customs'],
            'change': ['suppliers', 'purchases', 'payments', 'customs', 'inventory'],
            'delete': []
        },
        'auditor': {
            'view': ['all'],
            'add': [],
            'change': [],
            'delete': []
        }
    }
    
    role_perms = permissions.get(profile.role, {})
    allowed_models = role_perms.get(permission_type, [])
    
    if 'all' in allowed_models:
        return True
    
    return model_name in allowed_models if model_name else False