from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset, Div, HTML
from .models import Purchase, FreightCost, CustomsDeclaration
from suppliers.models import Supplier
from core.models import Currency
from core.utils import CurrencyConverter, TaxCalculator

class PurchaseForm(forms.ModelForm):
    
    class Meta:
        model = Purchase
        fields = [
            'purchase_date', 'supplier', 'purchase_price_fob', 
            'currency', 'exchange_rate_to_da', 'notes'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'purchase_price_fob': forms.NumberInput(attrs={'step': '0.01'}),
            'exchange_rate_to_da': forms.NumberInput(attrs={'step': '0.000001'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('purchase_date', css_class='form-group col-md-6'),
                Column('supplier', css_class='form-group col-md-6'),
            ),
            Row(
                Column('purchase_price_fob', css_class='form-group col-md-4'),
                Column('currency', css_class='form-group col-md-4'),
                Column('exchange_rate_to_da', css_class='form-group col-md-4'),
            ),
            HTML('<div class="alert alert-info"><small>Prix calculé en DA: <span id="calculated-price">0.00 DA</span></small></div>'),
            'notes',
            Row(
                Column(
                    Submit('submit', 'Enregistrer l\'achat', css_class='btn btn-primary'),
                    Reset('reset', 'Réinitialiser', css_class='btn btn-secondary'),
                    css_class='form-group col-md-12'
                )
            )
        )
        
        # Filter suppliers to active only
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        
        # Filter currencies to foreign ones
        self.fields['currency'].queryset = Currency.objects.filter(
            code__in=['USD', 'CNY'], is_active=True
        )
        
        # Try to get latest exchange rate
        if not self.instance.pk and self.data.get('currency'):
            try:
                currency = Currency.objects.get(pk=self.data['currency'])
                latest_rate = CurrencyConverter.get_latest_rate(currency.code)
                if latest_rate:
                    self.fields['exchange_rate_to_da'].initial = latest_rate
            except Currency.DoesNotExist:
                pass

class FreightCostForm(forms.ModelForm):
    
    class Meta:
        model = FreightCost
        fields = [
            'freight_method', 'freight_cost', 'freight_currency', 'freight_exchange_rate',
            'insurance_cost_da', 'other_logistics_costs_da'
        ]
        widgets = {
            'freight_cost': forms.NumberInput(attrs={'step': '0.01'}),
            'freight_exchange_rate': forms.NumberInput(attrs={'step': '0.000001'}),
            'insurance_cost_da': forms.NumberInput(attrs={'step': '0.01'}),
            'other_logistics_costs_da': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'freight_method',
            Row(
                Column('freight_cost', css_class='form-group col-md-4'),
                Column('freight_currency', css_class='form-group col-md-4'),
                Column('freight_exchange_rate', css_class='form-group col-md-4'),
            ),
            HTML('<div class="alert alert-info"><small>Coût de fret en DA: <span id="freight-cost-da">0.00 DA</span></small></div>'),
            Row(
                Column('insurance_cost_da', css_class='form-group col-md-6'),
                Column('other_logistics_costs_da', css_class='form-group col-md-6'),
            ),
            HTML('<div class="alert alert-success"><strong>Total des frais de transport: <span id="total-freight-cost">0.00 DA</span></strong></div>'),
            Row(
                Column(
                    Submit('submit', 'Enregistrer les frais de transport', css_class='btn btn-primary'),
                    css_class='form-group col-md-12'
                )
            )
        )

class CustomsDeclarationForm(forms.ModelForm):
    
    auto_calculate = forms.BooleanField(
        required=False, 
        initial=True,
        label="Calcul automatique des droits et taxes",
        help_text="Calculer automatiquement les droits d'importation et la TVA"
    )
    
    class Meta:
        model = CustomsDeclaration
        fields = [
            'declaration_date', 'declaration_number', 'cif_value_da',
            'customs_tariff_rate', 'import_duty_da', 'tva_rate', 'tva_amount_da',
            'other_fees_da', 'is_cleared', 'clearance_date', 'notes'
        ]
        widgets = {
            'declaration_date': forms.DateInput(attrs={'type': 'date'}),
            'clearance_date': forms.DateInput(attrs={'type': 'date'}),
            'cif_value_da': forms.NumberInput(attrs={'step': '0.01', 'readonly': True}),
            'customs_tariff_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'import_duty_da': forms.NumberInput(attrs={'step': '0.01'}),
            'tva_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'tva_amount_da': forms.NumberInput(attrs={'step': '0.01'}),
            'other_fees_da': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.purchase = kwargs.pop('purchase', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill CIF value
        if self.purchase and not self.instance.pk:
            self.fields['cif_value_da'].initial = self.calculate_cif_value()
            
            # Set default rates from settings
            self.fields['customs_tariff_rate'].initial = TaxCalculator.get_tariff_rate()
            self.fields['tva_rate'].initial = TaxCalculator.get_tva_rate()
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('declaration_date', css_class='form-group col-md-6'),
                Column('declaration_number', css_class='form-group col-md-6'),
            ),
            'cif_value_da',
            'auto_calculate',
            Row(
                Column('customs_tariff_rate', css_class='form-group col-md-6'),
                Column('import_duty_da', css_class='form-group col-md-6'),
            ),
            Row(
                Column('tva_rate', css_class='form-group col-md-6'),
                Column('tva_amount_da', css_class='form-group col-md-6'),
            ),
            'other_fees_da',
            HTML('<div class="alert alert-success"><strong>Total des frais douaniers: <span id="total-customs-cost">0.00 DA</span></strong></div>'),
            Row(
                Column('is_cleared', css_class='form-group col-md-6'),
                Column('clearance_date', css_class='form-group col-md-6'),
            ),
            'notes',
            Row(
                Column(
                    Submit('submit', 'Enregistrer la déclaration douanière', css_class='btn btn-primary'),
                    css_class='form-group col-md-12'
                )
            )
        )
    
    def calculate_cif_value(self):
        """Calculate CIF value from purchase and freight costs"""
        if not self.purchase:
            return 0
        
        purchase_price = self.purchase.purchase_price_da or 0
        freight_cost = getattr(self.purchase, 'freight_cost', None)
        freight_total = freight_cost.total_freight_cost_da if freight_cost else 0
        
        return purchase_price + freight_total
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Auto-calculate if requested
        if cleaned_data.get('auto_calculate'):
            cif_value = cleaned_data.get('cif_value_da', 0)
            tariff_rate = cleaned_data.get('customs_tariff_rate', 0)
            tva_rate = cleaned_data.get('tva_rate', 0)
            
            # Calculate import duty
            import_duty = cif_value * (tariff_rate / 100)
            cleaned_data['import_duty_da'] = import_duty
            
            # Calculate TVA
            taxable_base = cif_value + import_duty
            tva_amount = taxable_base * (tva_rate / 100)
            cleaned_data['tva_amount_da'] = tva_amount
        
        return cleaned_data

class PurchaseSearchForm(forms.Form):
    """Form for searching purchases"""
    
    search = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par fournisseur, numéro de déclaration...',
            'class': 'form-control'
        })
    )
    
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les fournisseurs",
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
    
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les devises",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    customs_status = forms.ChoiceField(
        choices=[
            ('', 'Tous'),
            ('pending', 'En cours de dédouanement'),
            ('cleared', 'Dédouané'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )