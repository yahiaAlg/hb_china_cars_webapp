# Django Models Compilation

This document contains all models from all Django apps in the project.

---

# Customers App

## customers/models.py

```
python
from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from core.models import BaseModel

class Customer(BaseModel):
    """Local Algerian customers"""

    CUSTOMER_TYPES = [
        ('individual', 'Particulier'),
        ('company', 'Entreprise'),
    ]

    # Algerian provinces (Wilayas) - major ones
    WILAYA_CHOICES = [
        ('01', 'Adrar'), ('02', 'Chlef'), ('03', 'Laghouat'), ('04', 'Oum El Bouaghi'),
        ('05', 'Batna'), ('06', 'Béjaïa'), ('07', 'Biskra'), ('08', 'Béchar'),
        ('09', 'Blida'), ('10', 'Bouira'), ('11', 'Tamanghasset'), ('12', 'Tébessa'),
        ('13', 'Tlemcen'), ('14', 'Tiaret'), ('15', 'Tizi Ouzou'), ('16', 'Alger'),
        ('17', 'Djelfa'), ('18', 'Jijel'), ('19', 'Sétif'), ('20', 'Saïda'),
        ('21', 'Skikda'), ('22', 'Sidi Bel Abbès'), ('23', 'Annaba'), ('24', 'Guelma'),
        ('25', 'Constantine'), ('26', 'Médéa'), ('27', 'Mostaganem'), ('28', 'M\'Sila'),
        ('29', 'Mascara'), ('30', 'Ouargla'), ('31', 'Oran'), ('32', 'El Bayadh'),
        ('33', 'Illizi'), ('34', 'Bordj Bou Arréridj'), ('35', 'Boumerdès'), ('36', 'El Tarf'),
        ('37', 'Tindouf'), ('38', 'Tissemsilt'), ('39', 'El Oued'), ('40', 'Khenchela'),
        ('41', 'Souk Ahras'), ('42', 'Tipaza'), ('43', 'Mila'), ('44', 'Aïn Defla'),
        ('45', 'Naâma'), ('46', 'Aïn Témouchent'), ('47', 'Ghardaïa'), ('48', 'Relizane'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom complet/Raison sociale")
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, verbose_name="Type de client")

    # Tax identification for companies
    nif_tax_id = models.CharField(
        max_length=20, blank=True,
        verbose_name="NIF/Numéro fiscal",
        help_text="Obligatoire pour les entreprises"
    )

    # Contact information
    phone = models.CharField(
        max_length=20,
        verbose_name="Téléphone",
        validators=[
            RegexValidator(
                regex=r'^(\+213|0)[1-9][0-9]{8}$',
                message="Format: +213XXXXXXXXX ou 0XXXXXXXXX"
            )
        ]
    )
    email = models.EmailField(blank=True, validators=[EmailValidator()])

    # Address
    address = models.TextField(verbose_name="Adresse")
    wilaya = models.CharField(max_length=2, choices=WILAYA_CHOICES, verbose_name="Wilaya")

    notes = models.TextField(blank=True, verbose_name="Notes")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_customer_type_display()})"

    def clean(self):
        """Validation"""
        super().clean()

        # NIF required for companies
        if self.customer_type == 'company' and not self.nif_tax_id:
            raise ValidationError({'nif_tax_id': 'Le NIF est obligatoire pour les entreprises.'})

        # Unique name or phone validation
        existing = Customer.objects.filter(
            models.Q(name__iexact=self.name) | models.Q(phone=self.phone)
        )
        if self.pk:
            existing = existing.exclude(pk=self.pk)

        if existing.exists():
            raise ValidationError('Un client avec ce nom ou ce téléphone existe déjà.')

    @property
    def total_purchases(self):
        """Get total number of vehicle purchases"""
        return self.sale_set.count()

    @property
    def total_purchase_value(self):
        """Get total purchase value in DA"""
        return sum(sale.sale_price for sale in self.sale_set.all())

    @property
    def outstanding_balance(self):
        """Get total outstanding balance from unpaid invoices"""
        return sum(
            invoice.balance_due
            for invoice in self.invoice_set.filter(balance_due__gt=0)
        )

    @property
    def last_purchase_date(self):
        """Get date of last purchase"""
        last_sale = self.sale_set.order_by('-sale_date').first()
        return last_sale.sale_date if last_sale else None

    def get_wilaya_display(self):
        """Get wilaya display name"""
        wilaya_dict = dict(self.WILAYA_CHOICES)
        return wilaya_dict.get(self.wilaya, self.wilaya)

    @property
    def is_company(self):
        return self.customer_type == 'company'

    @property
    def is_individual(self):
        return self.customer_type == 'individual'

class CustomerNote(BaseModel):
    """Notes and interactions with customers"""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_notes')
    note = models.TextField(verbose_name="Note")
    is_important = models.BooleanField(default=False, verbose_name="Important")

    class Meta:
        verbose_name = "Note client"
        verbose_name_plural = "Notes clients"
        ordering = ['-created_at']

    def __str__(self):
        return f"Note pour {self.customer.name} - {self.created_at.strftime('%d/%m/%Y')}"
```

---

# Commissions App

## commissions/models.py

```
python
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
from sales.models import Sale

class CommissionTier(BaseModel):
    """Commission tier configuration for performance-based rates"""

    name = models.CharField(max_length=50, verbose_name="Nom du niveau")
    min_sales_count = models.PositiveIntegerField(
        verbose_name="Nombre minimum de ventes"
    )
    max_sales_count = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Nombre maximum de ventes"
    )
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux de commission (%)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Niveau de commission"
        verbose_name_plural = "Niveaux de commission"
        ordering = ['min_sales_count']

    def __str__(self):
        if self.max_sales_count:
            return f"{self.name} ({self.min_sales_count}-{self.max_sales_count} ventes) - {self.commission_rate}%"
        else:
            return f"{self.name} ({self.min_sales_count}+ ventes) - {self.commission_rate}%"

    def applies_to_sales_count(self, sales_count):
        """Check if this tier applies to given sales count"""
        if sales_count < self.min_sales_count:
            return False
        if self.max_sales_count and sales_count > self.max_sales_count:
            return False
        return True

class CommissionPeriod(BaseModel):
    """Monthly commission calculation period"""

    year = models.PositiveIntegerField(verbose_name="Année")
    month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Mois"
    )
    is_closed = models.BooleanField(default=False, verbose_name="Période fermée")
    closed_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de fermeture")
    closed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='closed_commission_periods',
        verbose_name="Fermée par"
    )

    class Meta:
        verbose_name = "Période de commission"
        verbose_name_plural = "Périodes de commission"
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        months = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return f"{months[self.month]} {self.year}"

    def close_period(self, user):
        """Close the commission period"""
        self.is_closed = True
        self.closed_date = timezone.now()
        self.closed_by = user
        self.save()

        # Calculate final commissions for all traders
        self.calculate_period_commissions()

    def calculate_period_commissions(self):
        """Calculate commissions for all traders in this period"""
        from django.db.models import Sum, Count

        # Get all traders
        traders = User.objects.filter(
            userprofile__role__in=['trader', 'manager'],
            is_active=True
        )

        for trader in traders:
            # Get sales for this trader in this period
            sales = Sale.objects.filter(
                assigned_trader=trader,
                sale_date__year=self.year,
                sale_date__month=self.month,
                is_finalized=True
            )

            # Calculate totals
            sales_count = sales.count()
            total_commission = sales.aggregate(
                Sum('commission_amount')
            )['commission_amount__sum'] or 0

            # Get or create commission summary
            summary, created = CommissionSummary.objects.get_or_create(
                trader=trader,
                period=self,
                defaults={
                    'sales_count': sales_count,
                    'total_commission': total_commission,
                    'created_by': self.closed_by
                }
            )

            if not created:
                summary.sales_count = sales_count
                summary.total_commission = total_commission
                summary.updated_by = self.closed_by
                summary.save()

class CommissionSummary(BaseModel):
    """Monthly commission summary per trader"""

    PAYOUT_STATUS = [
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
    ]

    trader = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='commission_summaries',
        verbose_name="Trader"
    )
    period = models.ForeignKey(
        CommissionPeriod, on_delete=models.CASCADE,
        related_name='commission_summaries',
        verbose_name="Période"
    )

    # Performance metrics
    sales_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de ventes"
    )
    total_sales_value = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Valeur totale des ventes (DA)"
    )
    total_margin = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        verbose_name="Marge totale (DA)"
    )

    # Commission calculation
    base_commission = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Commission de base (DA)"
    )
    tier_bonus = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Bonus de niveau (DA)"
    )
    total_commission = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Commission totale (DA)"
    )

    # Payout tracking
    payout_status = models.CharField(
        max_length=20, choices=PAYOUT_STATUS,
        default='pending',
        verbose_name="Statut de paiement"
    )
    payout_date = models.DateField(
        null=True, blank=True,
        verbose_name="Date de paiement"
    )
    payout_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name="Référence de paiement"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Résumé de commission"
        verbose_name_plural = "Résumés de commission"
        unique_together = ['trader', 'period']
        ordering = ['-period__year', '-period__month', 'trader__first_name']

    def __str__(self):
        return f"{self.trader.get_full_name() or self.trader.username} - {self.period}"

    @property
    def average_commission_rate(self):
        """Calculate average commission rate"""
        if self.total_margin > 0:
            return (self.total_commission / self.total_margin) * 100
        return 0

    @property
    def average_sale_value(self):
        """Calculate average sale value"""
        if self.sales_count > 0:
            return self.total_sales_value / self.sales_count
        return 0

    def calculate_tier_bonus(self):
        """Calculate tier bonus based on sales count"""
        # Find applicable tier
        tier = CommissionTier.objects.filter(
            is_active=True
        ).filter(
            min_sales_count__lte=self.sales_count
        ).filter(
            models.Q(max_sales_count__gte=self.sales_count) |
            models.Q(max_sales_count__isnull=True)
        ).first()

        if tier:
            # Calculate bonus as difference from base rate
            base_rate = 10.0  # Default base rate
            if tier.commission_rate > base_rate:
                bonus_rate = tier.commission_rate - base_rate
                self.tier_bonus = self.total_margin * (bonus_rate / 100)
            else:
                self.tier_bonus = 0
        else:
            self.tier_bonus = 0

        self.total_commission = self.base_commission + self.tier_bonus
        return self.tier_bonus

class CommissionAdjustment(BaseModel):
    """Manual commission adjustments"""

    ADJUSTMENT_TYPES = [
        ('bonus', 'Bonus'),
        ('penalty', 'Pénalité'),
        ('correction', 'Correction'),
        ('special', 'Spécial'),
    ]

    trader = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='commission_adjustments',
        verbose_name="Trader"
    )
    period = models.ForeignKey(
        CommissionPeriod, on_delete=models.CASCADE,
        related_name='commission_adjustments',
        verbose_name="Période"
    )

    adjustment_type = models.CharField(
        max_length=20, choices=ADJUSTMENT_TYPES,
        verbose_name="Type d'ajustement"
    )
    amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Montant (DA)"
    )
    reason = models.TextField(verbose_name="Raison")

    approved_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='approved_adjustments',
        verbose_name="Approuvé par"
    )

    class Meta:
        verbose_name = "Ajustement de commission"
        verbose_name_plural = "Ajustements de commission"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_adjustment_type_display()} - {self.trader.get_full_name()} - {self.amount:,.2f} DA"

class CommissionPayment(BaseModel):
    """Commission payout records"""

    PAYMENT_METHODS = [
        ('bank_transfer', 'Virement Bancaire'),
        ('cash', 'Espèces'),
        ('check', 'Chèque'),
    ]

    summary = models.OneToOneField(
        CommissionSummary, on_delete=models.CASCADE,
        related_name='commission_payment',
        verbose_name="Résumé de commission"
    )

    payment_date = models.DateField(verbose_name="Date de paiement")
    amount_paid = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant payé (DA)"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS,
        verbose_name="Mode de paiement"
    )

    bank_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name="Référence bancaire"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    paid_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='commission_payments_made',
        verbose_name="Payé par"
    )

    class Meta:
        verbose_name = "Paiement de commission"
        verbose_name_plural = "Paiements de commission"
        ordering = ['-payment_date']

    def __str__(self):
        return f"Paiement commission - {self.summary.trader.get_full_name()} - {self.amount_paid:,.2f} DA"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update summary payout status
        self.summary.payout_status = 'paid'
        self.summary.payout_date = self.payment_date
        self.summary.payout_reference = self.bank_reference
        self.summary.save()
```

---

# Core App

## core/models.py

```
python
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
```

---

# Inventory App

## inventory/models.py

```
python
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from core.models import BaseModel
from purchases.models import Purchase
from decimal import Decimal

class Vehicle(BaseModel):
    """Vehicle inventory with status tracking"""

    STATUS_CHOICES = [
        ('in_transit', 'En Transit'),
        ('at_customs', 'En Douane'),
        ('available', 'Disponible'),
        ('reserved', 'Réservé'),
        ('sold', 'Vendu'),
    ]

    # Vehicle identification
    vin_chassis = models.CharField(
        max_length=50, unique=True,
        verbose_name="VIN/Numéro de châssis"
    )

    # Vehicle details
    make = models.CharField(max_length=100, verbose_name="Marque")
    model = models.CharField(max_length=100, verbose_name="Modèle")
    year = models.PositiveIntegerField(verbose_name="Année")
    color = models.CharField(max_length=50, verbose_name="Couleur")
    engine_type = models.CharField(max_length=100, blank=True, verbose_name="Type de moteur")
    specifications = models.TextField(blank=True, verbose_name="Spécifications")

    # Purchase information
    vehicle_purchase = models.ForeignKey(
        Purchase, on_delete=models.PROTECT,
        related_name='vehicle_set',
        verbose_name="Achat associé"
    )

    # Status and availability
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='in_transit',
        verbose_name="Statut"
    )

    # Reservation details (when status = 'reserved')
    reserved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reserved_vehicles',
        verbose_name="Réservé par"
    )
    reservation_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de réservation")
    reservation_expires = models.DateTimeField(null=True, blank=True, verbose_name="Expiration réservation")

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.make} {self.model} {self.year} - {self.vin_chassis}"

    def clean(self):
        """Validation"""
        super().clean()

        # VIN format validation (basic)
        if self.vin_chassis and len(self.vin_chassis) < 10:
            raise ValidationError({'vin_chassis': 'Le VIN/châssis doit contenir au moins 10 caractères.'})

        # Year validation
        current_year = timezone.now().year
        if self.year and (self.year < 2000 or self.year > current_year + 1):
            raise ValidationError({'year': f'L\'année doit être entre 2000 et {current_year + 1}.'})

    @property
    def landed_cost(self):
        """Calculate total landed cost from purchase"""
        purchase = self.vehicle_purchase

        # Base purchase price
        total_cost = purchase.purchase_price_da or 0

        # Add freight costs
        if hasattr(purchase, 'freight_cost'):
            total_cost += purchase.freight_cost.total_freight_cost_da or 0

        # Add customs costs
        if hasattr(purchase, 'customs_declaration'):
            total_cost += purchase.customs_declaration.total_customs_cost_da or 0

        return total_cost

    @property
    def is_available_for_sale(self):
        """Check if vehicle can be sold"""
        return self.status in ['available', 'reserved']

    @property
    def reservation_expired(self):
        """Check if reservation has expired"""
        if self.status != 'reserved' or not self.reservation_expires:
            return False
        return timezone.now() > self.reservation_expires

    def reserve_for_trader(self, trader, days=7):
        """Reserve vehicle for specific trader"""
        if self.status != 'available':
            raise ValueError("Vehicle is not available for reservation")

        self.status = 'reserved'
        self.reserved_by = trader
        self.reservation_date = timezone.now()
        self.reservation_expires = timezone.now() + timedelta(days=days)
        self.save()

    def release_reservation(self):
        """Release vehicle reservation"""
        if self.status == 'reserved':
            self.status = 'available'
            self.reserved_by = None
            self.reservation_date = None
            self.reservation_expires = None
            self.save()

    def mark_as_sold(self):
        """Mark vehicle as sold"""
        self.status = 'sold'
        self.reserved_by = None
        self.reservation_date = None
        self.reservation_expires = None
        self.save()

    @property
    def days_in_stock(self):
        """Calculate number of days in stock (since available status)"""
        if self.status not in ['available', 'reserved', 'sold']:
            return 0

        # Find when vehicle became available
        # For simplicity, use created_at if no better tracking available
        start_date = self.created_at.date()

        if self.status == 'sold':
            # Get sale date if available
            if hasattr(self, 'sale'):
                return (self.sale.sale_date - start_date).days

        return (timezone.now().date() - start_date).days

    @property
    def is_slow_moving(self, threshold_days=90):
        """Check if vehicle is slow-moving (in stock too long)"""
        return self.status == 'available' and self.days_in_stock > threshold_days

class VehiclePhoto(BaseModel):
    """Vehicle photos for documentation"""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='vehicle_photos/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False, verbose_name="Photo principale")

    class Meta:
        verbose_name = "Photo de véhicule"
        verbose_name_plural = "Photos de véhicules"

    def __str__(self):
        return f"Photo de {self.vehicle} - {self.caption}"

    def save(self, *args, **kwargs):
        # Ensure only one primary photo per vehicle
        if self.is_primary:
            VehiclePhoto.objects.filter(
                vehicle=self.vehicle, is_primary=True
            ).update(is_primary=False)

        super().save(*args, **kwargs)

class StockAlert(BaseModel):
    """Stock alerts and notifications"""

    ALERT_TYPES = [
        ('slow_moving', 'Véhicule à rotation lente'),
        ('reservation_expired', 'Réservation expirée'),
        ('customs_delayed', 'Retard en douane'),
        ('low_stock', 'Stock faible'),
    ]

    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Alerte de stock"
        verbose_name_plural = "Alertes de stock"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.vehicle or 'Général'}"

    def resolve(self, user):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()
```

---

# Payments App

## payments/models.py

```
python
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
from sales.models import Invoice

class Payment(BaseModel):
    """Customer payment record"""

    PAYMENT_METHODS = [
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement Bancaire'),
        ('check', 'Chèque'),
        ('card', 'Carte Bancaire'),
        ('other', 'Autre'),
    ]

    # Payment identification
    payment_number = models.CharField(
        max_length=20, unique=True,
        verbose_name="Numéro de paiement"
    )
    payment_date = models.DateField(verbose_name="Date de paiement")

    # Related invoice
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT,
        related_name='payments',
        verbose_name="Facture"
    )

    # Payment details
    amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Montant (DA)"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS,
        verbose_name="Mode de paiement"
    )

    # Reference information
    bank_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name="Référence bancaire/chèque"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    # Status
    is_confirmed = models.BooleanField(default=True, verbose_name="Confirmé")

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"Paiement {self.payment_number} - {self.amount:,.2f} DA"

    def clean(self):
        """Validation"""
        super().clean()

        # Payment date validation
        if self.payment_date and self.payment_date > timezone.now().date():
            raise ValidationError({'payment_date': 'La date de paiement ne peut pas être dans le futur.'})

        # Amount validation against invoice balance
        if self.invoice and self.amount:
            remaining_balance = self.invoice.balance_due
            if self.pk:  # If editing existing payment
                # Add back this payment's amount to get original balance
                remaining_balance += self.amount

            if self.amount > remaining_balance:
                raise ValidationError({
                    'amount': f'Le montant ne peut pas dépasser le solde dû ({remaining_balance:,.2f} DA).'
                })

    def save(self, *args, **kwargs):
        # Generate payment number if not set
        if not self.payment_number:
            self.payment_number = self.generate_payment_number()

        super().save(*args, **kwargs)

        # Update invoice payment status
        self.update_invoice_balance()

    def generate_payment_number(self):
        """Generate unique payment number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"PAY-{today.strftime('%Y%m%d')}"

        # Find last payment number for today
        last_payment = Payment.objects.filter(
            payment_number__startswith=prefix
        ).order_by('-payment_number').first()

        if last_payment:
            try:
                last_num = int(last_payment.payment_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:03d}"

    def update_invoice_balance(self):
        """Update related invoice balance and status"""
        if self.invoice:
            # Recalculate total payments for this invoice
            total_payments = self.invoice.payments.filter(
                is_confirmed=True
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or 0

            # Update invoice
            self.invoice.amount_paid = total_payments
            self.invoice.balance_due = self.invoice.total_ttc - total_payments

            # Update status
            if self.invoice.balance_due <= 0:
                self.invoice.status = 'paid'
            elif self.invoice.amount_paid > 0:
                self.invoice.status = 'issued'  # Partially paid

            self.invoice.save()

class PaymentReminder(BaseModel):
    """Payment reminder tracking"""

    REMINDER_TYPES = [
        ('email', 'Email'),
        ('phone', 'Téléphone'),
        ('sms', 'SMS'),
        ('letter', 'Courrier'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name="Facture"
    )

    reminder_date = models.DateField(verbose_name="Date de relance")
    reminder_type = models.CharField(
        max_length=20, choices=REMINDER_TYPES,
        verbose_name="Type de relance"
    )

    message = models.TextField(verbose_name="Message")
    sent_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        verbose_name="Envoyé par"
    )

    # Response tracking
    customer_response = models.TextField(
        blank=True,
        verbose_name="Réponse du client"
    )
    follow_up_date = models.DateField(
        null=True, blank=True,
        verbose_name="Date de suivi"
    )

    class Meta:
        verbose_name = "Relance de paiement"
        verbose_name_plural = "Relances de paiement"
        ordering = ['-reminder_date']

    def __str__(self):
        return f"Relance {self.get_reminder_type_display()} - {self.invoice.invoice_number}"

class PaymentPlan(BaseModel):
    """Installment payment plan"""

    PLAN_STATUS = [
        ('active', 'Actif'),
        ('completed', '
```
