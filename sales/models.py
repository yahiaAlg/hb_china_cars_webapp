from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
from inventory.models import Vehicle
from customers.models import Customer

class Sale(BaseModel):
    """Vehicle sale transaction"""
    
    PAYMENT_METHODS = [
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement Bancaire'),
        ('installment', 'Paiement Échelonné'),
        ('check', 'Chèque'),
    ]
    
    # Sale identification
    sale_number = models.CharField(
        max_length=20, unique=True, 
        verbose_name="Numéro de vente"
    )
    sale_date = models.DateField(verbose_name="Date de vente")
    
    # Parties involved
    vehicle = models.OneToOneField(
        Vehicle, on_delete=models.PROTECT,
        verbose_name="Véhicule"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT,
        verbose_name="Client"
    )
    assigned_trader = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='sales_as_trader',
        verbose_name="Trader assigné"
    )
    
    # Financial details
    sale_price = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix de vente (DA)"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS,
        verbose_name="Mode de paiement"
    )
    down_payment = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Acompte (DA)"
    )
    
    # Commission calculation
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux de commission (%)"
    )
    commission_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name="Montant commission (DA)"
    )
    
    # Status and notes
    is_finalized = models.BooleanField(default=False, verbose_name="Finalisée")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-sale_date', '-created_at']
    
    def __str__(self):
        return f"Vente {self.sale_number} - {self.vehicle} à {self.customer.name}"
    
    def clean(self):
        """Validation"""
        super().clean()
        
        # Sale date validation
        if self.sale_date and self.sale_date > timezone.now().date():
            raise ValidationError({'sale_date': 'La date de vente ne peut pas être dans le futur.'})
        
        # Vehicle availability check
        if self.vehicle and self.vehicle.status not in ['available', 'reserved']:
            raise ValidationError({'vehicle': 'Ce véhicule n\'est pas disponible à la vente.'})
        
        # Down payment validation
        if self.down_payment and self.down_payment > self.sale_price:
            raise ValidationError({'down_payment': 'L\'acompte ne peut pas dépasser le prix de vente.'})
        
        # Trader role validation
        if self.assigned_trader and hasattr(self.assigned_trader, 'userprofile'):
            if not self.assigned_trader.userprofile.is_trader and not self.assigned_trader.userprofile.is_manager:
                raise ValidationError({'assigned_trader': 'Seuls les traders et managers peuvent être assignés aux ventes.'})
    
    def save(self, *args, **kwargs):
        # Generate sale number if not set
        if not self.sale_number:
            self.sale_number = self.generate_sale_number()
        
        # Calculate commission
        if self.sale_price and self.commission_rate is not None:
            margin = self.calculate_margin()
            if margin > 0:
                self.commission_amount = margin * (self.commission_rate / 100)
            else:
                self.commission_amount = 0
        
        super().save(*args, **kwargs)
        
        # Update vehicle status
        if self.vehicle:
            self.vehicle.status = 'sold'
            self.vehicle.save()
    
    def generate_sale_number(self):
        """Generate unique sale number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"VTE-{today.strftime('%Y%m%d')}"
        
        # Find last sale number for today
        last_sale = Sale.objects.filter(
            sale_number__startswith=prefix
        ).order_by('-sale_number').first()
        
        if last_sale:
            try:
                last_num = int(last_sale.sale_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:03d}"
    
    @property
    def landed_cost(self):
        """Get vehicle landed cost"""
        return self.vehicle.landed_cost if self.vehicle else 0
    
    def calculate_margin(self):
        """Calculate sale margin"""
        return self.sale_price - self.landed_cost
    
    @property
    def margin_amount(self):
        """Get margin amount"""
        return self.calculate_margin()
    
    @property
    def margin_percentage(self):
        """Calculate margin percentage"""
        if self.landed_cost > 0:
            return (self.calculate_margin() / self.landed_cost) * 100
        return 0
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance after down payment"""
        return self.sale_price - self.down_payment

class Invoice(BaseModel):
    """Customer invoice for vehicle sale"""
    
    INVOICE_STATUS = [
        ('draft', 'Brouillon'),
        ('issued', 'Émise'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
    ]
    
    # Invoice identification
    invoice_number = models.CharField(
        max_length=20, unique=True,
        verbose_name="Numéro de facture"
    )
    invoice_date = models.DateField(verbose_name="Date de facture")
    due_date = models.DateField(verbose_name="Date d'échéance")
    
    # Related sale
    sale = models.OneToOneField(
        Sale, on_delete=models.PROTECT,
        verbose_name="Vente"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT,
        verbose_name="Client"
    )
    
    # Financial details
    subtotal_ht = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Sous-total HT (DA)"
    )
    tva_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=19.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux TVA (%)"
    )
    tva_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Montant TVA (DA)"
    )
    total_ttc = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Total TTC (DA)"
    )
    
    # Payment tracking
    amount_paid = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant payé (DA)"
    )
    balance_due = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Solde dû (DA)"
    )
    
    # Status
    status = models.CharField(
        max_length=20, choices=INVOICE_STATUS,
        default='draft',
        verbose_name="Statut"
    )
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-invoice_date', '-created_at']
    
    def __str__(self):
        return f"Facture {self.invoice_number} - {self.customer.name}"
    
    def clean(self):
        """Validation"""
        super().clean()
        
        if self.due_date and self.invoice_date and self.due_date < self.invoice_date:
            raise ValidationError({'due_date': 'La date d\'échéance ne peut pas être antérieure à la date de facture.'})
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not set
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate tax amounts
        self.calculate_tax_amounts()
        
        # Update balance
        self.balance_due = self.total_ttc - self.amount_paid
        
        # Update status based on payment
        if self.balance_due <= 0:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'issued'  # Partially paid
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"INV-{today.strftime('%Y%m%d')}"
        
        # Find last invoice number for today
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            try:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:03d}"
    
    def calculate_tax_amounts(self):
        """Calculate tax amounts from sale price"""
        if self.sale:
            # Calculate HT from TTC
            self.total_ttc = self.sale.sale_price
            self.subtotal_ht = self.total_ttc / (1 + (self.tva_rate / 100))
            self.tva_amount = self.total_ttc - self.subtotal_ht
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return (
            self.status in ['issued'] and 
            self.due_date < timezone.now().date() and 
            self.balance_due > 0
        )
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0