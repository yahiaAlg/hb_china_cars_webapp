from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from .models import CommissionTier, CommissionAdjustment, CommissionPayment, CommissionSummary
from django.contrib.auth.models import User

class CommissionTierForm(forms.ModelForm):
    
    class Meta:
        model = CommissionTier
        fields = [
            'name', 'min_sales_count', 'max_sales_count',
            'commission_rate', 'is_active'
        ]
        widgets = {
            'commission_rate': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            Row(
                Column('min_sales_count', css_class='form-group col-md-6'),
                Column('max_sales_count', css_class='form-group col-md-6'),
            ),
            Row(
                Column('commission_rate', css_class='form-group col-md-6'),
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

class CommissionAdjustmentForm(forms.ModelForm):
    
    class Meta:
        model = CommissionAdjustment
        fields = [
            'trader', 'adjustment_type', 'amount', 'reason'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.period = kwargs.pop('period', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('trader', css_class='form-group col-md-6'),
                Column('adjustment_type', css_class='form-group col-md-6'),
            ),
            'amount',
            'reason',
            Submit('submit', 'Enregistrer l\'Ajustement', css_class='btn btn-primary')
        )
        
        # Filter traders
        self.fields['trader'].queryset = User.objects.filter(
            userprofile__role__in=['trader', 'manager'],
            is_active=True
        )
    
    def save(self, commit=True):
        adjustment = super().save(commit=False)
        
        if self.period:
            adjustment.period = self.period
        
        if commit:
            adjustment.save()
        
        return adjustment

class CommissionPaymentForm(forms.ModelForm):
    
    class Meta:
        model = CommissionPayment
        fields = [
            'payment_date', 'amount_paid', 'payment_method',
            'bank_reference', 'notes'
        ]
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'amount_paid': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.summary = kwargs.pop('summary', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('payment_date', css_class='form-group col-md-6'),
                Column('payment_method', css_class='form-group col-md-6'),
            ),
            'amount_paid',
            'bank_reference',
            'notes',
            Submit('submit', 'Enregistrer le Paiement', css_class='btn btn-success')
        )
        
        # Pre-fill amount with commission total
        if self.summary and not self.instance.pk:
            self.fields['amount_paid'].initial = self.summary.total_commission
            
            # Set today as default date
            from django.utils import timezone
            self.fields['payment_date'].initial = timezone.now().date()
    
    def save(self, commit=True):
        payment = super().save(commit=False)
        
        if self.summary:
            payment.summary = self.summary
        
        if commit:
            payment.save()
        
        return payment

class CommissionReportForm(forms.Form):
    """Form for commission report filters"""
    
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    month = forms.ChoiceField(
        choices=[('', 'Tous les mois')] + [
            (i, month) for i, month in enumerate([
                '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
            ], 0) if month
        ],
        required=False,
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
    
    payout_status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + CommissionSummary.PAYOUT_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set current year as default
        if not self.data.get('year'):
            from django.utils import timezone
            self.fields['year'].initial = timezone.now().year

class TraderPerformanceFilterForm(forms.Form):
    """Filter form for trader performance comparison"""
    
    period_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'})
    )
    
    period_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'})
    )
    
    min_sales = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Nombre min de ventes',
            'class': 'form-control'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('total_commission', 'Commission totale'),
            ('sales_count', 'Nombre de ventes'),
            ('total_margin', 'Marge totale'),
            ('average_commission_rate', 'Taux moyen'),
        ],
        initial='total_commission',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default period (last 6 months)
        if not self.data.get('period_from'):
            from django.utils import timezone
            from dateutil.relativedelta import relativedelta
            
            today = timezone.now().date()
            six_months_ago = today - relativedelta(months=6)
            
            self.fields['period_from'].initial = six_months_ago.replace(day=1)
            self.fields['period_to'].initial = today.replace(day=1)