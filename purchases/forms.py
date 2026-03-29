from django import forms
from django.forms import inlineformset_factory
from .models import Purchase, PurchaseLineItem, FreightCost, CustomsDeclaration
from suppliers.models import Supplier
from core.models import Currency
from core.utils import TaxCalculator


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            "purchase_date",
            "supplier",
            "currency",
            "exchange_rate_to_da",
            "notes",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
            "exchange_rate_to_da": forms.NumberInput(attrs={"step": "0.000001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True)
        self.fields["currency"].queryset = Currency.objects.filter(
            code__in=["USD", "CNY"], is_active=True
        )
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, (forms.Select,)):
                w.attrs.setdefault("class", "field-select")
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault("class", "field-input field-textarea")
            else:
                w.attrs.setdefault("class", "field-input")
        if not self.instance.pk:
            from django.utils import timezone

            self.fields["purchase_date"].initial = timezone.now().date()


class PurchaseLineItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseLineItem
        fields = [
            "make",
            "model",
            "year",
            "color",
            "engine_type",
            "vin_chassis",
            "fob_price",
            "notes",
        ]
        widgets = {
            "make": forms.TextInput(attrs={"placeholder": "ex. BYD"}),
            "model": forms.TextInput(attrs={"placeholder": "ex. Atto 3"}),
            "year": forms.NumberInput(attrs={"placeholder": "2025", "min": "2000"}),
            "color": forms.TextInput(attrs={"placeholder": "ex. Blanc"}),
            "engine_type": forms.TextInput(attrs={"placeholder": "ex. Électrique"}),
            "vin_chassis": forms.TextInput(attrs={"placeholder": "Optionnel"}),
            "fob_price": forms.NumberInput(
                attrs={"step": "0.01", "placeholder": "0.00"}
            ),
            "notes": forms.TextInput(attrs={"placeholder": "Notes (facultatif)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["engine_type"].required = False
        self.fields["vin_chassis"].required = False
        self.fields["notes"].required = False


# Default 4 rows (typical container), minimum 1 required
PurchaseLineItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseLineItem,
    form=PurchaseLineItemForm,
    extra=4,
    min_num=1,
    validate_min=True,
    can_delete=True,
    fields=[
        "make",
        "model",
        "year",
        "color",
        "engine_type",
        "vin_chassis",
        "fob_price",
        "notes",
    ],
)


class FreightCostForm(forms.ModelForm):
    class Meta:
        model = FreightCost
        fields = [
            "freight_method",
            "freight_cost",
            "freight_currency",
            "freight_exchange_rate",
            "insurance_cost_da",
            "other_logistics_costs_da",
        ]
        widgets = {
            "freight_cost": forms.NumberInput(attrs={"step": "0.01"}),
            "freight_exchange_rate": forms.NumberInput(attrs={"step": "0.000001"}),
            "insurance_cost_da": forms.NumberInput(attrs={"step": "0.01"}),
            "other_logistics_costs_da": forms.NumberInput(attrs={"step": "0.01"}),
        }


class CustomsDeclarationForm(forms.ModelForm):
    auto_calculate = forms.BooleanField(
        required=False, initial=True, label="Calcul automatique des droits et taxes"
    )

    class Meta:
        model = CustomsDeclaration
        fields = [
            "declaration_date",
            "declaration_number",
            "cif_value_da",
            "customs_tariff_rate",
            "import_duty_da",
            "tva_rate",
            "tva_amount_da",
            "other_fees_da",
            "is_cleared",
            "clearance_date",
            "notes",
        ]
        widgets = {
            "declaration_date": forms.DateInput(attrs={"type": "date"}),
            "clearance_date": forms.DateInput(attrs={"type": "date"}),
            "cif_value_da": forms.NumberInput(attrs={"step": "0.01", "readonly": True}),
            "customs_tariff_rate": forms.NumberInput(attrs={"step": "0.01"}),
            "import_duty_da": forms.NumberInput(attrs={"step": "0.01"}),
            "tva_rate": forms.NumberInput(attrs={"step": "0.01"}),
            "tva_amount_da": forms.NumberInput(attrs={"step": "0.01"}),
            "other_fees_da": forms.NumberInput(attrs={"step": "0.01"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.purchase = kwargs.pop("purchase", None)
        super().__init__(*args, **kwargs)
        if self.purchase:
            self.fields["cif_value_da"].initial = self._calc_cif()
            if not self.instance.pk:
                self.fields["customs_tariff_rate"].initial = (
                    TaxCalculator.get_tariff_rate()
                )
                self.fields["tva_rate"].initial = TaxCalculator.get_tva_rate()

    def _calc_cif(self):
        from decimal import Decimal

        fob = self.purchase.total_fob_da or Decimal("0")
        fc = getattr(self.purchase, "freight_cost", None)
        return fob + (fc.total_freight_cost_da if fc else Decimal("0"))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("auto_calculate"):
            cif = cleaned_data.get("cif_value_da", 0)
            tariff = cleaned_data.get("customs_tariff_rate", 0)
            tva_r = cleaned_data.get("tva_rate", 0)
            duty = round(cif * (tariff / 100), 2)
            tva = round((cif + duty) * (tva_r / 100), 2)
            cleaned_data["import_duty_da"] = duty
            cleaned_data["tva_amount_da"] = tva
        return cleaned_data


class PurchaseSearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Fournisseur, N° déclaration…",
                "class": "form-control",
            }
        ),
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les fournisseurs",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    customs_status = forms.ChoiceField(
        choices=[("", "Tous"), ("pending", "En cours"), ("cleared", "Dédouané")],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
