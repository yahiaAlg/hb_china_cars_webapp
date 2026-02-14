from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset, HTML
from .models import Sale, Invoice
from inventory.models import Vehicle
from customers.models import Customer
from django.contrib.auth.models import User

class SaleForm(forms.ModelForm):
    
    class Meta:
        model = Sale
        fields = [
            'sale_date', 'vehicle', 'customer', 'assigned_trader',
            'sale_price', 'payment_method', 'down_payment',
            'commission_rate', 'notes'
        ]
        widgets = {
            'sale_date': forms.DateInput(attrs={'type': 'date'}),
            'sale_price': forms.NumberInput(attrs={'step': '0.01'}),
            'down_payment': forms.NumberInput(attrs={'step': '0.01'}),
            'commission_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('sale_date', css_class='form-group col-md-6'),
                Column('payment_method', css_class='form-group col-md-6'),
            ),
            Row(
                Column('vehicle', css_class='form-group col-md-6'),
                Column('customer', css_class='form-group col-md-6'),
            ),
            Row(
                Column('sale_price', css_class='form-group col-md-4'),
                Column('down_payment', css_class='form-group col-md-4'),
                Column('commission_rate', css_class='form-group col-md-4'),
            ),
            'assigned_trader',
            HTML('<div id="margin-calculation" class="alert alert-info" style="display:none;"></div>'),
            'notes',
            Row(
                Column(
                    Submit('submit', 'Enregistrer la Vente', css_class='btn btn-primary'),
                    Reset('reset', 'Réinitialiser', css_class='btn btn-secondary'),
                    css_class='form-group col-md-12'
                )
            )
        )
        
        # Filter available vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            status__in=['available', 'reserved']
        ).select_related('vehicle_purchase__supplier')
        
        # Filter active customers
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        
        # Filter traders
        self.fields['assigned_trader'].queryset = User.objects.filter(
            userprofile__role__in=['trader', 'manager'],
            is_active=True
        )
        
        # Set default values
        if not self.instance.pk:
            # Set current user as default trader if they are a trader
            if self.user and hasattr(self.user, 'userprofile'):
                if self.user.userprofile.is_trader:
                    self.fields['assigned_trader'].initial = self.user
                    self.fields['commission_rate'].initial = self.user.userprofile.default_commission_rate
        
        # Set today as default date
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['sale_date'].initial = timezone.now().date()

class InvoiceForm(forms.ModelForm):
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_date', 'due_date', 'tva_rate', 'notes'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'tva_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('invoice_date', css_class='form-group col-md-6'),
                Column('due_date', css_class='form-group col-md-6'),
            ),
            'tva_rate',
            'notes',
            Row(
                Column(
                    Submit('submit', 'Générer la Facture', css_class='btn btn-primary'),
                    css_class='form-group col-md-12'
                )
            )
        )
        
        # Set default dates
        if not self.instance.pk:
            from django.utils import timezone
            from datetime import timedelta
            today = timezone.now().date()
            self.fields['invoice_date'].initial = today
            self.fields['due_date'].initial = today + timedelta(days=30)

class SaleSearchForm(forms.Form):
    """Form for searching sales"""
    
    search = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par numéro, client, véhicule...',
            'class': 'form-control'
        })
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
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'Tous les modes')] + Sale.PAYMENT_METHODS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_finalized = forms.ChoiceField(
        choices=[
            ('', 'Tous'),
            ('true', 'Finalisées seulement'),
            ('false', 'Brouillons seulement'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class QuickSaleForm(forms.ModelForm):
    """Simplified form for quick sales"""
    
    class Meta:
        model = Sale
        fields = ['vehicle', 'customer', 'sale_price', 'payment_method']
        widgets = {
            'sale_price': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'vehicle',
            'customer', 
            'sale_price',
            'payment_method',
            Submit('submit', 'Vente Rapide', css_class='btn btn-success')
        )
        
        # Filter available vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            status='available'
        )
        
        # Filter active customers
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
    
    def save(self, commit=True):
        sale = super().save(commit=False)
        
        # Set defaults
        if self.user:
            sale.assigned_trader = self.user
            if hasattr(self.user, 'userprofile'):
                sale.commission_rate = self.user.userprofile.default_commission_rate
        
        from django.utils import timezone
        sale.sale_date = timezone.now().date()
        
        if commit:
            sale.save()
        
        return sale