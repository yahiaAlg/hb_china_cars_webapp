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