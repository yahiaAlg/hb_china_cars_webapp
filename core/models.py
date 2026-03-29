from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class UserProfile(models.Model):
    """Extended user profile for role-based permissions"""
    
    ROLE_CHOICES = [
        ('manager', 'Manager/Admin'),
        ('trader', 'Trader/Sales'),
        ('finance', 'Finance/Inventory'),
        ('auditor', 'Read-Only/Audit'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    default_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default commission rate percentage for this trader"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_trader(self):
        return self.role == 'trader'
    
    @property
    def is_finance(self):
        return self.role == 'finance'
    
    @property
    def is_auditor(self):
        return self.role == 'auditor'

class Currency(models.Model):
    """Currency master data"""
    
    code = models.CharField(max_length=3, unique=True, help_text="ISO currency code")
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class ExchangeRate(models.Model):
    """Exchange rates for currency conversion"""
    
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='from_rates')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='to_rates')
    rate = models.DecimalField(max_digits=15, decimal_places=6, validators=[MinValueValidator(0)])
    effective_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
        unique_together = ['from_currency', 'to_currency', 'effective_date']
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"1 {self.from_currency.code} = {self.rate} {self.to_currency.code} ({self.effective_date})"

class SystemSetting(models.Model):
    """System-wide configuration settings"""
    
    SETTING_TYPES = [
        ('decimal', 'Decimal'),
        ('integer', 'Integer'),
        ('string', 'String'),
        ('boolean', 'Boolean'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"{self.key} = {self.value}"
    
    def get_value(self):
        """Return the value in the correct type"""
        if self.setting_type == 'decimal':
            return Decimal(self.value)
        elif self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes']
        return self.value

class BaseModel(models.Model):
    """Abstract base model with common fields"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name='%(class)s_created', 
        null=True, blank=True
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name='%(class)s_updated', 
        null=True, blank=True
    )
    
    class Meta:
        abstract = True