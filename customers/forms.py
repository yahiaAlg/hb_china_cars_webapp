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
            "notes",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter full name or company name",
                }
            ),
            "customer_type": forms.Select(
                attrs={"class": "form-select", "id": "customerType"}
            ),
            "nif_tax_id": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter NIF number",
                    "id": "nifInput",
                }
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "+213 XXX XXX XXX"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-input", "placeholder": "customer@email.dz"}
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 3,
                    "placeholder": "Street address",
                }
            ),
            "wilaya": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 4,
                    "placeholder": "Add any additional notes about the customer...",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamic field requirements based on customer type
        if self.data.get("customer_type") == "company":
            self.fields["nif_tax_id"].required = True


class CustomerSearchForm(forms.Form):
    """Form for searching customers"""

    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search for a client...",
                "class": "filter-input",
                "type": "text",
            }
        ),
    )

    customer_type = forms.ChoiceField(
        choices=[("", "All types")] + Customer.CUSTOMER_TYPES,
        required=False,
        widget=forms.Select(attrs={"class": "filter-select"}),
    )

    wilaya = forms.ChoiceField(
        choices=[("", "All wilayas")] + Customer.WILAYA_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "filter-select"}),
    )

    is_active = forms.ChoiceField(
        choices=[
            ("", "All"),
            ("true", "Active only"),
            ("false", "Inactive only"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "filter-select"}),
    )

    has_outstanding = forms.BooleanField(
        required=False,
        label="With unpaid balance",
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
                    "placeholder": "Add a note about this customer...",
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
                attrs={"class": "form-input", "placeholder": "Customer name"}
            ),
            "customer_type": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "+213 XXX XXX XXX"}
            ),
            "address": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "wilaya": forms.Select(attrs={"class": "form-select"}),
            "nif_tax_id": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "NIF (if applicable)"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields
        self.fields["name"].required = True
        self.fields["phone"].required = True
        self.fields["address"].required = True
        self.fields["wilaya"].required = True
