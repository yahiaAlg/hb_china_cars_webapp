from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from .models import Supplier
from core.models import Currency

class SupplierForm(forms.ModelForm):
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'country', 'contact_person', 'phone', 'email', 
            'address', 'currency', 'payment_terms', 'notes', 'is_active'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'payment_terms': forms.TextInput(attrs={'placeholder': 'ex: 30% avance, 70% à la livraison'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-8'),
                Column('country', css_class='form-group col-md-4'),
            ),
            Row(
                Column('contact_person', css_class='form-group col-md-6'),
                Column('currency', css_class='form-group col-md-6'),
            ),
            Row(
                Column('phone', css_class='form-group col-md-6'),
                Column('email', css_class='form-group col-md-6'),
            ),
            'address',
            'payment_terms',
            'notes',
            Row(
                Column('is_active', css_class='form-group col-md-6'),
            ),
            Row(
                Column(
                    Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
                    Reset('reset', 'Réinitialiser', css_class='btn btn-secondary'),
                    css_class='form-group col-md-12'
                )
            )
        )
        
        # Limit currency choices to foreign currencies
        self.fields['currency'].queryset = Currency.objects.filter(
            code__in=['USD', 'CNY'], is_active=True
        )
        
        # Set default country
        if not self.instance.pk:
            self.fields['country'].initial = 'Chine'

class SupplierSearchForm(forms.Form):
    """Form for searching and filtering suppliers"""
    
    search = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par nom, contact, email...',
            'class': 'form-control'
        })
    )
    
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les devises",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Tous'),
            ('true', 'Actifs seulement'),
            ('false', 'Inactifs seulement'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )