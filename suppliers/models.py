from django.db import models
from django.core.validators import EmailValidator
from core.models import BaseModel, Currency

class Supplier(BaseModel):
    """Chinese car suppliers/exporters"""
    
    name = models.CharField(max_length=200, unique=True, verbose_name="Nom du fournisseur")
    country = models.CharField(max_length=100, default="Chine")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Personne de contact")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone/WhatsApp")
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    address = models.TextField(blank=True, verbose_name="Adresse")
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, 
        limit_choices_to={'code__in': ['USD', 'CNY']},
        verbose_name="Devise par défaut"
    )
    payment_terms = models.CharField(max_length=200, blank=True, verbose_name="Conditions de paiement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validation: At least one contact method required"""
        from django.core.exceptions import ValidationError
        
        if not self.phone and not self.email:
            raise ValidationError("Au moins un moyen de contact (téléphone ou email) est requis.")
    
    @property
    def has_purchases(self):
        """Check if supplier has any vehicle purchases"""
        return self.purchase_set.exists()
    
    def get_total_purchases(self):
        """Get total number of vehicles purchased from this supplier"""
        return self.purchase_set.count()
    
    def get_total_purchase_value(self):
        """Get total purchase value in DA"""
        return sum(
            purchase.purchase_price_da 
            for purchase in self.purchase_set.all()
            if purchase.purchase_price_da
        )