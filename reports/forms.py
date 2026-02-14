from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from django.contrib.auth.models import User
from customers.models import Customer
from suppliers.models import Supplier

class ProfitAnalysisForm(forms.Form):
    """Form for profit analysis report filters"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    trader = forms.ModelChoiceField(
        queryset=User.objects.filter(
            userprofile__role__in=['trader', 'manager'],
            is_active=True
        ),
        required=False,
        empty_label="Tous les traders",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les clients",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    vehicle_make = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Marque de véhicule',
            'class': 'form-control'
        })
    )
    
    min_margin = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'placeholder': 'Marge minimum (DA)',
            'class': 'form-control'
        })
    )
    
    group_by = forms.ChoiceField(
        choices=[
            ('month', 'Par mois'),
            ('trader', 'Par trader'),
            ('customer', 'Par client'),
            ('vehicle_make', 'Par marque'),
        ],
        initial='month',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('date_from', css_class='form-group col-md-6'),
                Column('date_to', css_class='form-group col-md-6'),
            ),
            Row(
                Column('trader', css_class='form-group col-md-6'),
                Column('customer', css_class='form-group col-md-6'),
            ),
            Row(
                Column('vehicle_make', css_class='form-group col-md-6'),
                Column('min_margin', css_class='form-group col-md-6'),
            ),
            'group_by',
            Submit('submit', 'Générer le Rapport', css_class='btn btn-primary')
        )
        
        # Set default date range (last 3 months)
        if not self.data.get('date_from'):
            from django.utils import timezone
            from dateutil.relativedelta import relativedelta
            
            today = timezone.now().date()
            three_months_ago = today - relativedelta(months=3)
            
            self.fields['date_from'].initial = three_months_ago
            self.fields['date_to'].initial = today

class InventoryStatusForm(forms.Form):
    """Form for inventory status report filters"""
    
    status = forms.MultipleChoiceField(
        choices=[
            ('in_transit', 'En Transit'),
            ('at_customs', 'En Douane'),
            ('available', 'Disponible'),
            ('reserved', 'Réservé'),
            ('sold', 'Vendu'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les fournisseurs",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    vehicle_make = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Marque de véhicule',
            'class': 'form-control'
        })
    )
    
    year_from = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Année min',
            'class': 'form-control'
        })
    )
    
    year_to = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Année max',
            'class': 'form-control'
        })
    )
    
    min_landed_cost = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'placeholder': 'Coût minimum (DA)',
            'class': 'form-control'
        })
    )
    
    max_landed_cost = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'placeholder': 'Coût maximum (DA)',
            'class': 'form-control'
        })
    )
    
    days_in_stock_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Jours min en stock',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'status',
            Row(
                Column('supplier', css_class='form-group col-md-6'),
                Column('vehicle_make', css_class='form-group col-md-6'),
            ),
            Row(
                Column('year_from', css_class='form-group col-md-6'),
                Column('year_to', css_class='form-group col-md-6'),
            ),
            Row(
                Column('min_landed_cost', css_class='form-group col-md-6'),
                Column('max_landed_cost', css_class='form-group col-md-6'),
            ),
            'days_in_stock_min',
            Submit('submit', 'Générer le Rapport', css_class='btn btn-primary')
        )

class SalesSummaryForm(forms.Form):
    """Form for sales summary report filters"""
    
    period_type = forms.ChoiceField(
        choices=[
            ('daily', 'Quotidien'),
            ('weekly', 'Hebdomadaire'),
            ('monthly', 'Mensuel'),
            ('quarterly', 'Trimestriel'),
            ('yearly', 'Annuel'),
        ],
        initial='monthly',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    trader = forms.ModelChoiceField(
        queryset=User.objects.filter(
            userprofile__role__in=['trader', 'manager'],
            is_active=True
        ),
        required=False,
        empty_label="Tous les traders",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'Tous les modes')] + [
            ('cash', 'Espèces'),
            ('bank_transfer', 'Virement Bancaire'),
            ('installment', 'Paiement Échelonné'),
            ('check', 'Chèque'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        label="Inclure les graphiques",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'period_type',
            Row(
                Column('date_from', css_class='form-group col-md-6'),
                Column('date_to', css_class='form-group col-md-6'),
            ),
            Row(
                Column('trader', css_class='form-group col-md-6'),
                Column('payment_method', css_class='form-group col-md-6'),
            ),
            'include_charts',
            Submit('submit', 'Générer le Rapport', css_class='btn btn-primary')
        )
        
        # Set default date range (last 12 months)
        if not self.data.get('date_from'):
            from django.utils import timezone
            from dateutil.relativedelta import relativedelta
            
            today = timezone.now().date()
            twelve_months_ago = today - relativedelta(months=12)
            
            self.fields['date_from'].initial = twelve_months_ago
            self.fields['date_to'].initial = today

class PaymentStatusForm(forms.Form):
    """Form for payment status report filters"""
    
    invoice_status = forms.MultipleChoiceField(
        choices=[
            ('issued', 'Émise'),
            ('paid', 'Payée'),
            ('cancelled', 'Annulée'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    overdue_only = forms.BooleanField(
        required=False,
        label="Factures en retard seulement",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    days_overdue_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Jours de retard minimum',
            'class': 'form-control'
        })
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les clients",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    trader = forms.ModelChoiceField(
        queryset=User.objects.filter(
            userprofile__role__in=['trader', 'manager'],
            is_active=True
        ),
        required=False,
        empty_label="Tous les traders",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'placeholder': 'Montant minimum (DA)',
            'class': 'form-control'
        })
    )
    
    amount_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'placeholder': 'Montant maximum (DA)',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'invoice_status',
            Row(
                Column('overdue_only', css_class='form-group col-md-6'),
                Column('days_overdue_min', css_class='form-group col-md-6'),
            ),
            Row(
                Column('customer', css_class='form-group col-md-6'),
                Column('trader', css_class='form-group col-md-6'),
            ),
            Row(
                Column('amount_min', css_class='form-group col-md-6'),
                Column('amount_max', css_class='form-group col-md-6'),
            ),
            Submit('submit', 'Générer le Rapport', css_class='btn btn-primary')
        )

class ReportExportForm(forms.Form):
    """Form for report export options"""
    
    EXPORT_FORMATS = [
        ('excel', 'Excel (.xlsx)'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    ]
    
    format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        initial='excel',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        label="Inclure les graphiques (PDF seulement)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    email_to = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Envoyer par email (optionnel)',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'format',
            'include_charts',
            'email_to',
            Submit('submit', 'Exporter', css_class='btn btn-success')
        )