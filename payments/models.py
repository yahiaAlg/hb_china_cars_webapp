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
        ('completed', 'Terminé'),
        ('defaulted', 'En défaut'),
        ('cancelled', 'Annulé'),
    ]
    
    invoice = models.OneToOneField(
        Invoice, on_delete=models.CASCADE,
        related_name='payment_plan',
        verbose_name="Facture"
    )
    
    total_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Montant total (DA)"
    )
    down_payment = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Acompte (DA)"
    )
    remaining_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Montant restant (DA)"
    )
    
    number_of_installments = models.PositiveIntegerField(
        verbose_name="Nombre d'échéances"
    )
    installment_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Montant par échéance (DA)"
    )
    
    start_date = models.DateField(verbose_name="Date de début")
    status = models.CharField(
        max_length=20, choices=PLAN_STATUS,
        default='active',
        verbose_name="Statut"
    )
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Plan de paiement"
        verbose_name_plural = "Plans de paiement"
    
    def __str__(self):
        return f"Plan de paiement - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        # Calculate remaining amount and installment amount
        self.remaining_amount = self.total_amount - self.down_payment
        if self.number_of_installments > 0:
            self.installment_amount = self.remaining_amount / self.number_of_installments
        
        super().save(*args, **kwargs)
        
        # Create installment records
        if not self.pk:  # Only on creation
            self.create_installments()
    
    def create_installments(self):
        """Create individual installment records"""
        from dateutil.relativedelta import relativedelta
        
        current_date = self.start_date
        for i in range(self.number_of_installments):
            Installment.objects.create(
                payment_plan=self,
                installment_number=i + 1,
                due_date=current_date,
                amount=self.installment_amount,
                created_by=self.created_by
            )
            current_date += relativedelta(months=1)  # Monthly installments

class Installment(BaseModel):
    """Individual installment in payment plan"""
    
    INSTALLMENT_STATUS = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('overdue', 'En retard'),
        ('partial', 'Partiellement payé'),
    ]
    
    payment_plan = models.ForeignKey(
        PaymentPlan, on_delete=models.CASCADE,
        related_name='installments',
        verbose_name="Plan de paiement"
    )
    
    installment_number = models.PositiveIntegerField(
        verbose_name="Numéro d'échéance"
    )
    due_date = models.DateField(verbose_name="Date d'échéance")
    amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Montant (DA)"
    )
    
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
    
    status = models.CharField(
        max_length=20, choices=INSTALLMENT_STATUS,
        default='pending',
        verbose_name="Statut"
    )
    
    payment_date = models.DateField(
        null=True, blank=True,
        verbose_name="Date de paiement"
    )
    
    class Meta:
        verbose_name = "Échéance"
        verbose_name_plural = "Échéances"
        ordering = ['due_date', 'installment_number']
        unique_together = ['payment_plan', 'installment_number']
    
    def __str__(self):
        return f"Échéance {self.installment_number} - {self.payment_plan.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        # Calculate balance due
        self.balance_due = self.amount - self.amount_paid
        
        # Update status
        if self.balance_due <= 0:
            self.status = 'paid'
            if not self.payment_date:
                self.payment_date = timezone.now().date()
        elif self.amount_paid > 0:
            self.status = 'partial'
        elif self.due_date < timezone.now().date():
            self.status = 'overdue'
        else:
            self.status = 'pending'
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        return (
            self.status in ['pending', 'partial'] and
            self.due_date < timezone.now().date()
        )
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0