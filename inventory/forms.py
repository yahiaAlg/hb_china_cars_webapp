from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from .models import Vehicle, VehiclePhoto
from purchases.models import PurchaseLineItem


class VehicleForm(forms.ModelForm):

    class Meta:
        model = Vehicle
        fields = [
            "vin_chassis",
            "make",
            "model",
            "year",
            "color",
            "engine_type",
            "specifications",
            "purchase_line_item",
        ]

    widgets = {
        "vin_chassis": forms.TextInput(attrs={"class": "form-input"}),
        "make": forms.TextInput(attrs={"class": "form-input"}),
        "model": forms.TextInput(attrs={"class": "form-input"}),
        "year": forms.NumberInput(attrs={"class": "form-input"}),
        "color": forms.TextInput(attrs={"class": "form-input"}),
        "engine_type": forms.TextInput(attrs={"class": "form-input"}),
        "specifications": forms.Textarea(attrs={"rows": 4, "class": "form-textarea"}),
        "purchase_line_item": forms.Select(attrs={"class": "form-select"}),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set classes directly on widget instances — guaranteed to apply
        self.fields["vin_chassis"].widget.attrs["class"] = "form-input"
        self.fields["make"].widget.attrs["class"] = "form-input"
        self.fields["model"].widget.attrs["class"] = "form-input"
        self.fields["year"].widget.attrs["class"] = "form-input"
        self.fields["color"].widget.attrs["class"] = "form-input"
        self.fields["engine_type"].widget.attrs["class"] = "form-input"
        self.fields["specifications"].widget.attrs["class"] = "form-textarea"
        self.fields["purchase_line_item"].widget.attrs["class"] = "form-select"
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "vin_chassis",
            Row(
                Column("make", css_class="form-group col-md-4"),
                Column("model", css_class="form-group col-md-4"),
                Column("year", css_class="form-group col-md-4"),
            ),
            Row(
                Column("color", css_class="form-group col-md-6"),
                Column("engine_type", css_class="form-group col-md-6"),
            ),
            "purchase_line_item",
            "specifications",
            Row(
                Column(
                    Submit("submit", "Enregistrer", css_class="btn btn-primary"),
                    Reset("reset", "Réinitialiser", css_class="btn btn-secondary"),
                    css_class="form-group col-md-12",
                )
            ),
        )

        # Filter purchases to show only those without vehicles or current vehicle
        # After
        if self.instance.pk:
            self.fields["purchase_line_item"].queryset = (
                PurchaseLineItem.objects.filter(
                    Q(vehicle__isnull=True) | Q(vehicle=self.instance)
                )
            )
        else:
            self.fields["purchase_line_item"].queryset = (
                PurchaseLineItem.objects.filter(vehicle__isnull=True)
            )


class VehicleSearchForm(forms.Form):
    """Form for searching vehicles"""

    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Rechercher par VIN, marque, modèle...",
                "class": "form-control",
            }
        ),
    )

    status = forms.ChoiceField(
        choices=[("", "Tous les statuts")] + Vehicle.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    make = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Marque"}
        ),
    )

    year_from = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Année min"}
        ),
    )

    year_to = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Année max"}
        ),
    )

    trader = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Tous les traders",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User

        super().__init__(*args, **kwargs)

        # Filter traders only
        self.fields["trader"].queryset = User.objects.filter(
            userprofile__role="trader", is_active=True
        )


class VehiclePhotoForm(forms.ModelForm):
    class Meta:
        model = VehiclePhoto
        fields = ["photo", "caption", "is_primary"]
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"class": "field-input"}),
            "caption": forms.TextInput(attrs={"class": "field-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "photo",
            "caption",
            "is_primary",
            Submit("submit", "Ajouter Photo", css_class="btn btn-primary"),
        )


class ReservationForm(forms.Form):
    """Form for vehicle reservation"""

    DURATION_CHOICES = [
        (3, "3 jours"),
        (7, "7 jours"),
        (14, "14 jours"),
    ]

    duration_days = forms.ChoiceField(
        choices=[(3, "3 jours"), (7, "7 jours"), (14, "14 jours")],
        initial=7,
        label="Durée de réservation",
        widget=forms.Select(attrs={"class": "field-select"}),
    )

    notes = forms.CharField(
        max_length=500,
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={"class": "field-input", "rows": 3}),
    )
