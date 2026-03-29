from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from .models import Payment, PaymentReminder, PaymentPlan
from sales.models import Invoice


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = [
            "payment_date",
            "invoice",
            "amount",
            "payment_method",
            "bank_reference",
            "notes",
        ]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("payment_date", css_class="form-group col-md-6"),
                Column("payment_method", css_class="form-group col-md-6"),
            ),
            Row(
                Column("invoice", css_class="form-group col-md-8"),
                Column("amount", css_class="form-group col-md-4"),
            ),
            "bank_reference",
            "notes",
            Row(
                Column(
                    Submit(
                        "submit", "Enregistrer le Paiement", css_class="btn btn-primary"
                    ),
                    Reset("reset", "Réinitialiser", css_class="btn btn-secondary"),
                    css_class="form-group col-md-12",
                )
            ),
        )

        # When editing, include the current invoice even if fully paid
        if self.instance.pk and self.instance.invoice_id:
            from django.db.models import Q

            self.fields["invoice"].queryset = Invoice.objects.filter(
                Q(balance_due__gt=0) | Q(pk=self.instance.invoice_id)
            ).select_related("customer", "sale")
        else:
            self.fields["invoice"].queryset = Invoice.objects.filter(
                balance_due__gt=0
            ).select_related("customer", "sale")

        if not self.instance.pk:
            from django.utils import timezone

            self.fields["payment_date"].initial = timezone.now().date()


class QuickPaymentForm(forms.ModelForm):
    """Simplified payment form for quick entry"""

    class Meta:
        model = Payment
        fields = ["amount", "payment_method", "bank_reference"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop("invoice", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            "amount",
            "payment_method",
            "bank_reference",
            Submit("submit", "Enregistrer", css_class="btn btn-success"),
        )

        # Pre-fill amount with invoice balance
        if self.invoice and not self.instance.pk:
            self.fields["amount"].initial = self.invoice.balance_due

    def save(self, commit=True):
        payment = super().save(commit=False)

        if self.invoice:
            payment.invoice = self.invoice

        from django.utils import timezone

        payment.payment_date = timezone.now().date()

        if commit:
            payment.save()

        return payment


class PaymentSearchForm(forms.Form):
    """Form for searching payments"""

    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Rechercher par numéro, client, facture...",
                "class": "form-control",
            }
        ),
    )

    customer = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Nom du client", "class": "form-control"}
        ),
    )

    payment_method = forms.ChoiceField(
        choices=[("", "Tous les modes")] + Payment.PAYMENT_METHODS,
        required=False,
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

    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
    )

    amount_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
    )


class PaymentReminderForm(forms.ModelForm):

    class Meta:
        model = PaymentReminder
        fields = [
            "reminder_date",
            "reminder_type",
            "message",
            "customer_response",
            "follow_up_date",
        ]
        widgets = {
            "reminder_date": forms.DateInput(attrs={"type": "date"}),
            "follow_up_date": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4}),
            "customer_response": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("reminder_date", css_class="form-group col-md-6"),
                Column("reminder_type", css_class="form-group col-md-6"),
            ),
            "message",
            "customer_response",
            "follow_up_date",
            Submit("submit", "Enregistrer la Relance", css_class="btn btn-primary"),
        )

        # Set today as default date
        if not self.instance.pk:
            from django.utils import timezone

            self.fields["reminder_date"].initial = timezone.now().date()


class PaymentPlanForm(forms.ModelForm):

    class Meta:
        model = PaymentPlan
        fields = [
            "total_amount",
            "down_payment",
            "number_of_installments",
            "start_date",
            "notes",
        ]
        widgets = {
            "total_amount": forms.NumberInput(attrs={"step": "0.01"}),
            "down_payment": forms.NumberInput(attrs={"step": "0.01"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop("invoice", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("total_amount", css_class="form-group col-md-6"),
                Column("down_payment", css_class="form-group col-md-6"),
            ),
            Row(
                Column("number_of_installments", css_class="form-group col-md-6"),
                Column("start_date", css_class="form-group col-md-6"),
            ),
            "notes",
            Submit("submit", "Créer le Plan de Paiement", css_class="btn btn-primary"),
        )

        # Pre-fill with invoice amount
        if self.invoice and not self.instance.pk:
            self.fields["total_amount"].initial = self.invoice.balance_due

            # Set start date to next month
            from django.utils import timezone
            from dateutil.relativedelta import relativedelta

            next_month = timezone.now().date() + relativedelta(months=1)
            self.fields["start_date"].initial = next_month.replace(day=1)

    def save(self, commit=True):
        plan = super().save(commit=False)

        if self.invoice:
            plan.invoice = self.invoice

        if commit:
            plan.save()

        return plan


class OutstandingInvoicesFilterForm(forms.Form):
    """Filter form for outstanding invoices report"""

    customer = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Nom du client", "class": "form-control"}
        ),
    )

    trader = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Tous les traders",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    overdue_only = forms.BooleanField(
        required=False,
        label="Factures en retard seulement",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    days_overdue_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"placeholder": "Jours de retard min", "class": "form-control"}
        ),
    )

    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "placeholder": "Montant min (DA)",
                "class": "form-control",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User

        super().__init__(*args, **kwargs)

        # Filter traders only
        self.fields["trader"].queryset = User.objects.filter(
            userprofile__role__in=["trader", "manager"], is_active=True
        )
