from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from .models import Vehicle, VehiclePhoto
from purchases.models import Purchase

class VehicleForm(forms.ModelForm):
    
    class Meta:
        model = Vehicle
        fields = [
            'vin_chassis', 'make', 'model', 'year', 'color', 
            'engine_type', 'specifications', 'vehicle_purchase'
        ]
        widgets = {
            'specifications': forms.Textarea(attrs={'rows': 4}),
            'year': forms.NumberInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'vin_chassis',
            Row(
                Column('make', css_class='form-group col-md-4'),
                Column('model', css_class='form-group col-md-4'),
                Column('year', css_class='form-group col-md-4'),
            ),
            Row(
                Column('color', css_class='form-group col-md-6'),
                Column('engine_type', css_class='form-group col-md-6'),
            ),
            'vehicle_purchase',
            'specifications',
            Row(
                Column(
                    Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
                    Reset('reset', 'Réinitialiser', css_class='btn btn-secondary'),
                    css_class='form-group col-md-12'
                )
            )
        )
        
        # Filter purchases to show only those without vehicles or current vehicle
        if self.instance.pk:
            self.fields['vehicle_purchase'].queryset = Purchase.objects.filter(
                models.Q(vehicle__isnull=True) | models.Q(vehicle=self.instance)
            )
        else:
            self.fields['vehicle_purchase'].queryset = Purchase.objects.filter(vehicle__isnull=True)

class VehicleSearchForm(forms.Form):
    """Form for searching vehicles"""
    
    search = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par VIN, marque, modèle...',
            'class': 'form-control'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Vehicle.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    make = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marque'})
    )
    
    year_from = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Année min'})
    )
    
    year_to = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Année max'})
    )
    
    trader = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Tous les traders",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User
        super().__init__(*args, **kwargs)
        
        # Filter traders only
        self.fields['trader'].queryset = User.objects.filter(
            userprofile__role='trader',
            is_active=True
        )

class VehiclePhotoForm(forms.ModelForm):
    
    class Meta:
        model = VehiclePhoto
        fields = ['photo', 'caption', 'is_primary']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'photo',
            'caption',
            'is_primary',
            Submit('submit', 'Ajouter Photo', css_class='btn btn-primary')
        )

class ReservationForm(forms.Form):
    """Form for vehicle reservation"""
    
    DURATION_CHOICES = [
        (3, '3 jours'),
        (7, '7 jours'),
        (14, '14 jours'),
    ]
    
    duration_days = forms.ChoiceField(
        choices=DURATION_CHOICES,
        initial=7,
        label="Durée de réservation",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )