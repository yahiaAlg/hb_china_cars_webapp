from django import forms
from .models import Customer, CustomerNote


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = [
            "name",
            "customer_type",
            "nif_tax_id",
            "phone",
            "email",
            "address",
            "wilaya",
            "profile_photo",
            "passport_document",
            "notes",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nom complet ou raison sociale",
                }
            ),
            "customer_type": forms.Select(
                attrs={"class": "form-select", "id": "customerType"}
            ),
            "nif_tax_id": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "NIF", "id": "nifInput"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "+213 XXX XXX XXX"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-input", "placeholder": "client@exemple.dz"}
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 3,
                    "placeholder": "Rue, quartier, commune…",
                }
            ),
            "wilaya": forms.Select(attrs={"class": "form-select"}),
            "profile_photo": forms.FileInput(
                attrs={"class": "form-file-input", "accept": "image/*"}
            ),
            "passport_document": forms.FileInput(
                attrs={"class": "form-file-input", "accept": ".pdf,image/*"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 4,
                    "placeholder": "Remarques internes…",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get("customer_type") == "company":
            self.fields["nif_tax_id"].required = True


class CustomerSearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Rechercher…", "class": "filter-input"}
        ),
    )
    customer_type = forms.ChoiceField(
        choices=[("", "Tous les types")] + Customer.CUSTOMER_TYPES,
        required=False,
        widget=forms.Select(attrs={"class": "filter-select"}),
    )
    wilaya = forms.ChoiceField(
        choices=[("", "Toutes les wilayas")] + Customer.WILAYA_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "filter-select"}),
    )
    is_active = forms.ChoiceField(
        choices=[("", "Tous"), ("true", "Actif"), ("false", "Inactif")],
        required=False,
        widget=forms.Select(attrs={"class": "filter-select"}),
    )
    has_outstanding = forms.BooleanField(
        required=False,
        label="Solde impayé",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ["note", "is_important"]
        widgets = {
            "note": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-textarea",
                    "placeholder": "Ajouter une note…",
                }
            ),
            "is_important": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class QuickCustomerForm(forms.ModelForm):
    """Simplified form for quick customer creation during sales"""

    class Meta:
        model = Customer
        fields = ["name", "customer_type", "phone", "address", "wilaya", "nif_tax_id"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Nom du client"}
            ),
            "customer_type": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "+213 XXX XXX XXX"}
            ),
            "address": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "wilaya": forms.Select(attrs={"class": "form-select"}),
            "nif_tax_id": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "NIF (si applicable)"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["phone"].required = True
        self.fields["address"].required = True
        self.fields["wilaya"].required = True
