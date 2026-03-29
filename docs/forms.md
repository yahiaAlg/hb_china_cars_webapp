# Django Forms Compilation

This document contains all forms from all Django apps in the project.

---

# Customers App

## customers/forms.py

```
python
from django import forms
from .models import Customer, CustomerNote


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "customer_type", "nif_tax_id", "phone", "email", "address", "wilaya", "notes", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Enter full name or company name"}),
            "customer_type": forms.Select(attrs={"class": "form-select", "id": "customerType"}),
            "nif_tax_id": forms.TextInput(attrs={"class": "form-input", "placeholder": "Enter NIF number", "id": "nifInput"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "placeholder": "+213 XXX XXX XXX"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "customer@email.dz"}),
            "address": forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "placeholder": "Street address"}),
            "wilaya": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 4, "placeholder": "Additional notes..."}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get("customer_type") == "company":
            self.fields["nif_tax_id"].required = True


class CustomerSearchForm(forms.Form):
    """Form for searching customers"""
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={"placeholder": "Search for a client...", "class": "filter-input", "type": "text"}))
    customer_type = forms.ChoiceField(choices=[("", "All types")] + Customer.CUSTOMER_TYPES, required=False, widget=forms.Select(attrs={"class": "filter-select"}))
    wilaya = forms.ChoiceField(choices=[("", "All wilayas")] + Customer.WILAYA_CHOICES, required=False, widget=forms.Select(attrs={"class": "filter-select"}))
    is_active = forms.ChoiceField(choices=[("", "All"), ("true", "Active only"), ("false", "Inactive only")], required=False, widget=forms.Select(attrs={"class": "filter-select"}))
    has_outstanding = forms.BooleanField(required=False, label="With unpaid balance", widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))


class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ["note", "is_important"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 4, "class": "form-textarea", "placeholder": "Add a note about this customer..."}),
            "is_important": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class QuickCustomerForm(forms.ModelForm):
    """Simplified form for quick customer creation during sales"""
    class Meta:
        model = Customer
        fields = ["name", "customer_type", "phone", "address", "wilaya", "nif_tax_id"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Customer name"}),
            "customer_type": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "placeholder": "+213 XXX XXX XXX"}),
            "address": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "wilaya": forms.Select(attrs={"class": "form-select"}),
            "nif_tax_id": forms.TextInput(attrs={"class": "form-input", "placeholder": "NIF (if applicable)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["phone"].required = True
        self.fields["address"].required = True
        self.fields["wilaya"].required = True
```

---

# Commissions App

## commissions/forms.py

```
python
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from .models import CommissionTier, CommissionAdjustment, CommissionPayment, CommissionSummary
from django.contrib.auth.models import User

class CommissionTierForm(forms.ModelForm):
    class Meta:
        model = CommissionTier
        fields = ['name', 'min_sales_count', 'max_sales_count', 'commission_rate', 'is_active']
        widgets = {'commission_rate': forms.NumberInput(attrs={'step': '0.01'})}


class CommissionAdjustmentForm(forms.ModelForm):
    class Meta:
        model = CommissionAdjustment
        fields = ['trader', 'adjustment_type', 'amount', 'reason']
        widgets = {'amount': forms.NumberInput(attrs={'step': '0.01'}), 'reason': forms.Textarea(attrs={'rows': 3})}


class CommissionPaymentForm(forms.ModelForm):
    class Meta:
        model = CommissionPayment
        fields = ['payment_date', 'amount_paid', 'payment_method', 'bank_reference', 'notes']
        widgets = {'payment_date': forms.DateInput(attrs={'type': 'date'}), 'amount_paid': forms.NumberInput(attrs={'step': '0.01'}), 'notes': forms.Textarea(attrs={'rows': 3})}


class CommissionReportForm(forms.Form):
    """Form for commission report filters"""
    year = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    month = forms.ChoiceField(choices=[('', 'Tous les mois')] + [(i, month) for i, month in enumerate(['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'], 0) if month], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    trader = forms.ModelChoiceField(queryset=User.objects.filter(userprofile__role__in=['trader', 'manager'], is_active=True), required=False, empty_label="Tous les traders", widget=forms.Select(attrs={'class': 'form-control'}))
    payout_status = forms.ChoiceField(choices=[('', 'Tous les statuts')] + CommissionSummary.PAYOUT_STATUS, required=False, widget=forms.Select(attrs={'class': 'form-control'}))


class TraderPerformanceFilterForm(forms.Form):
    """Filter form for trader performance comparison"""
    period_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}))
    period_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}))
    min_sales = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Nombre min de ventes', 'class': 'form-control'}))
    sort_by = forms.ChoiceField(choices=[('total_commission', 'Commission totale'), ('sales_count', 'Nombre de ventes'), ('total_margin', 'Marge totale'), ('average_commission_rate', 'Taux moyen')], initial='total_commission', widget=forms.Select(attrs={'class': 'form-control'}))
```

---

# Inventory App

## inventory/forms.py

```
python
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from .models import Vehicle, VehiclePhoto
from purchases.models import Purchase

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vin_chassis', 'make', 'model', 'year', 'color', 'engine_type', 'specifications', 'vehicle_purchase']
        widgets = {'specifications': forms.Textarea(attrs={'rows': 4}), 'year': forms.NumberInput()}


class VehicleSearchForm(forms.Form):
    """Form for searching vehicles"""
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Rechercher par VIN, marque, modèle...', 'class': 'form-control'}))
    status = forms.ChoiceField(choices=[('', 'Tous les statuts')] + Vehicle.STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    make = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marque'}))
    year_from = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Année min'}))
    year_to = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Année max'}))
    trader = forms.ModelChoiceField(queryset=None, required=False, empty_label="Tous les traders", widget=forms.Select(attrs={'class': 'form-control'}))


class VehiclePhotoForm(forms.ModelForm):
    class Meta:
        model = VehiclePhoto
        fields = ['photo', 'caption', 'is_primary']


class ReservationForm(forms.Form):
    """Form for vehicle reservation"""
    DURATION_CHOICES = [(3, '3 jours'), (7, '7 jours'), (14, '14 jours')]
    duration_days = forms.ChoiceField(choices=DURATION_CHOICES, initial=7, label="Durée de réservation", widget=forms.Select(attrs={'class': 'form-control'}))
    notes = forms.CharField(max_length=500, required=False, label="Notes", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
```

---

# Payments App

## payments/forms.py

```
python
from django import forms
from .models import Payment, PaymentReminder, PaymentPlan
from sales.models import Invoice

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_date', 'invoice', 'amount', 'payment_method', 'bank_reference', 'notes']
        widgets = {'payment_date': forms.DateInput(attrs={'type': 'date'}), 'amount': forms.NumberInput(attrs={'step': '0.01'}), 'notes': forms.Textarea(attrs={'rows': 3})}


class QuickPaymentForm(forms.ModelForm):
    """Simplified payment form for quick entry"""
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'bank_reference']
        widgets = {'amount': forms.NumberInput(attrs={'step': '0.01'})}


class PaymentSearchForm(forms.Form):
    """Form for searching payments"""
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Rechercher par numéro, client, facture...', 'class': 'form-control'}))
    customer = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Nom du client', 'class': 'form-control'}))
    payment_method = forms.ChoiceField(choices=[('', 'Tous les modes')] + Payment.PAYMENT_METHODS, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    amount_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}))
    amount_max = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}))


class PaymentReminderForm(forms.ModelForm):
    class Meta:
        model = PaymentReminder
        fields = ['reminder_date', 'reminder_type', 'message', 'customer_response', 'follow_up_date']
        widgets = {'reminder_date': forms.DateInput(attrs={'type': 'date'}), 'follow_up_date': forms.DateInput(attrs={'type': 'date'}), 'message': forms.Textarea(attrs={'rows': 4}), 'customer_response': forms.Textarea(attrs={'rows': 3})}


class PaymentPlanForm(forms.ModelForm):
    class Meta:
        model = PaymentPlan
        fields = ['total_amount', 'down_payment', 'number_of_installments', 'start_date', 'notes']
        widgets = {'total_amount': forms.NumberInput(attrs={'step': '0.01'}), 'down_payment': forms.NumberInput(attrs={'step': '0.01'}), 'start_date': forms.DateInput(attrs={'type': 'date'}), 'notes': forms.Textarea(attrs={'rows': 3})}


class OutstandingInvoicesFilterForm(forms.Form):
    """Filter form for outstanding invoices report"""
    customer = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Nom du client', 'class': 'form-control'}))
    trader = forms.ModelChoiceField(queryset=None, required=False, empty_label="Tous les traders", widget=forms.Select(attrs={'class': 'form-control'}))
    overdue_only = forms.BooleanField(required=False, label="Factures en retard seulement", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    days_overdue_min = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Jours de retard min', 'class': 'form-control'}))
    amount_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Montant min (DA)', 'class': 'form-control'}))
```

---

# Purchases App

## purchases/forms.py

```
python
from django import forms
from .models import Purchase, FreightCost, CustomsDeclaration
from suppliers.models import Supplier
from core.models import Currency
from core.utils import CurrencyConverter, TaxCalculator

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['purchase_date', 'supplier', 'purchase_price_fob', 'currency', 'exchange_rate_to_da', 'notes']
        widgets = {'purchase_date': forms.DateInput(attrs={'type': 'date'}), 'notes': forms.Textarea(attrs={'rows': 3}), 'purchase_price_fob': forms.NumberInput(attrs={'step': '0.01'}), 'exchange_rate_to_da': forms.NumberInput(attrs={'step': '0.000001'})}


class FreightCostForm(forms.ModelForm):
    class Meta:
        model = FreightCost
        fields = ['freight_method', 'freight_cost', 'freight_currency', 'freight_exchange_rate', 'insurance_cost_da', 'other_logistics_costs_da']
        widgets = {'freight_cost': forms.NumberInput(attrs={'step': '0.01'}), 'freight_exchange_rate': forms.NumberInput(attrs={'step': '0.000001'}), 'insurance_cost_da': forms.NumberInput(attrs={'step': '0.01'}), 'other_logistics_costs_da': forms.NumberInput(attrs={'step': '0.01'})}


class CustomsDeclarationForm(forms.ModelForm):
    auto_calculate = forms.BooleanField(required=False, initial=True, label="Calcul automatique des droits et taxes")
    class Meta:
        model = CustomsDeclaration
        fields = ['declaration_date', 'declaration_number', 'cif_value_da', 'customs_tariff_rate', 'import_duty_da', 'tva_rate', 'tva_amount_da', 'other_fees_da', 'is_cleared', 'clearance_date', 'notes']
        widgets = {'declaration_date': forms.DateInput(attrs={'type': 'date'}), 'clearance_date': forms.DateInput(attrs={'type': 'date'}), 'cif_value_da': forms.NumberInput(attrs={'step': '0.01', 'readonly': True}), 'customs_tariff_rate': forms.NumberInput(attrs={'step': '0.01'}), 'import_duty_da': forms.NumberInput(attrs={'step': '0.01'}), 'tva_rate': forms.NumberInput(attrs={'step': '0.01'}), 'tva_amount_da': forms.NumberInput(attrs={'step': '0.01'}), 'other_fees_da': forms.NumberInput(attrs={'step': '0.01'}), 'notes': forms.Textarea(attrs={'rows': 3})}


class PurchaseSearchForm(forms.Form):
    """Form for searching purchases"""
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Rechercher par fournisseur, numéro de déclaration...', 'class': 'form-control'}))
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.filter(is_active=True), required=False, empty_label="Tous les fournisseurs", widget=forms.Select(attrs={'class': 'form-control'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    currency = forms.ModelChoiceField(queryset=Currency.objects.filter(is_active=True), required=False, empty_label="Toutes les devises", widget=forms.Select(attrs={'class': 'form-control'}))
    customs_status = forms.ChoiceField(choices=[('', 'Tous'), ('pending', 'En cours de dédouanement'), ('cleared', 'Dédouané')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
```

---

# Reports App

## reports/forms.py

```
python
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from django.contrib.auth.models import User
from customers.models import Customer
from suppliers.models import Supplier

class ProfitAnalysisForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    trader = forms.ModelChoiceField(queryset=User.objects.filter(userprofile__role__in=['trader', 'manager'], is_active=True), required=False, empty_label="Tous les traders", widget=forms.Select(attrs={'class': 'form-control'}))
    customer = forms.ModelChoiceField(queryset=Customer.objects.filter(is_active=True), required=False, empty_label="Tous les clients", widget=forms.Select(attrs={'class': 'form-control'}))
    vehicle_make = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Marque de véhicule', 'class': 'form-control'}))
    min_margin = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Marge minimum (DA)', 'class': 'form-control'}))
    group_by = forms.ChoiceField(choices=[('month', 'Par mois'), ('trader', 'Par trader'), ('customer', 'Par client'), ('vehicle_make', 'Par marque')], initial='month', widget=forms.Select(attrs={'class': 'form-control'}))


class InventoryStatusForm(forms.Form):
    status = forms.MultipleChoiceField(choices=[('in_transit', 'En Transit'), ('at_customs', 'En Douane'), ('available', 'Disponible'), ('reserved', 'Réservé'), ('sold', 'Vendu')], required=False, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}))
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.filter(is_active=True), required=False, empty_label="Tous les fournisseurs", widget=forms.Select(attrs={'class': 'form-control'}))
    vehicle_make = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Marque de véhicule', 'class': 'form-control'}))
    year_from = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Année min', 'class': 'form-control'}))
    year_to = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Année max', 'class': 'form-control'}))
    min_landed_cost = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Coût minimum (DA)', 'class': 'form-control'}))
    max_landed_cost = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Coût maximum (DA)', 'class': 'form-control'}))
    days_in_stock_min = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Jours min en stock', 'class': 'form-control'}))


class SalesSummaryForm(forms.Form):
    period_type = forms.ChoiceField(choices=[('daily', 'Quotidien'), ('weekly', 'Hebdomadaire'), ('monthly', 'Mensuel'), ('quarterly', 'Trimestriel'), ('yearly', 'Annuel')], initial='monthly', widget=forms.Select(attrs={'class': 'form-control'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    trader = forms.ModelChoiceField(queryset=User.objects.filter(userprofile__role__in=['trader', 'manager'], is_active=True), required=False, empty_label="Tous les traders", widget=forms.Select(attrs={'class': 'form-control'}))
    payment_method = forms.ChoiceField(choices=[('', 'Tous les modes')] + [('cash', 'Espèces'), ('bank_transfer', 'Virement Bancaire'), ('installment', 'Paiement Échelonné'), ('check', 'Chèque')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    include_charts = forms.BooleanField(required=False, initial=True, label="Inclure les graphiques", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))


class PaymentStatusForm(forms.Form):
    invoice_status = forms.MultipleChoiceField(choices=[('issued', 'Émise'), ('paid', 'Payée'), ('cancelled', 'Annulée')], required=False, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}))
    overdue_only = forms.BooleanField(required=False, label="Factures en retard seulement", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    days_overdue_min = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Jours de retard minimum', 'class': 'form-control'}))
    customer = forms.ModelChoiceField(queryset=Customer.objects.filter(is_active=True), required=False, empty_label="Tous les clients", widget=forms.Select(attrs={'class': 'form-control'}))
    trader = forms.ModelChoiceField(queryset=User.objects.filter(userprofile__role__in=['trader', 'manager'], is_active=True), required=False, empty_label="Tous les traders", widget=forms.Select(attrs={'class': 'form-control'}))
    amount_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Montant minimum (DA)', 'class': 'form-control'}))
    amount_max = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Montant maximum (DA)', 'class': 'form-control'}))


class ReportExportForm(forms.Form):
    EXPORT_FORMATS = [('excel', 'Excel (.xlsx)'), ('csv', 'CSV'), ('pdf', 'PDF')]
    format = forms.ChoiceField(choices=EXPORT_FORMATS, initial='excel', widget=forms.Select(attrs={'class': 'form-control'}))
    include_charts = forms.BooleanField(required=False, initial=True, label="Inclure les graphiques (PDF seulement)", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    email_to = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'placeholder': 'Envoyer par email (optionnel)', 'class': 'form-control'}))
```

---

# Sales App

## sales/forms.py

```
python
from django import forms
from .models import Sale, Invoice
from inventory.models import Vehicle
from customers.models import Customer
from django.contrib.auth.models import User

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['sale_date', 'vehicle', 'customer', 'assigned_trader', 'sale_price', 'payment_method', 'down_payment', 'commission_rate', 'notes']
        widgets = {'sale_date': forms.DateInput(attrs={'type': 'date'}), 'sale_price': forms.NumberInput(attrs={'step': '0.01'}), 'down_payment': forms.NumberInput(attrs={'step': '0.01'}), 'commission_rate': forms.NumberInput(attrs={'step': '0.01'}), 'notes': forms.Textarea(attrs={'rows': 3})}


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_date', 'due_date', 'tva_rate', 'notes']
        widgets = {'invoice_date': forms.DateInput(attrs={'type': 'date'}), 'due_date': forms.DateInput(attrs={'type': 'date'}), 'tva_rate': forms.NumberInput(attrs={'step': '0.01'}), 'notes': forms.Textarea(attrs={'rows': 3})}


class SaleSearchForm(forms.Form):
    """Form for searching sales"""
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Rechercher par numéro, client, véhicule...', 'class': 'form-control'}))
    trader = forms.ModelChoiceField(queryset=User.objects.filter(userprofile__role__in=['trader', 'manager'], is_active=True), required=False, empty_label="Tous les traders", widget=forms.Select(attrs={'class': 'form-control'}))
    customer = forms.ModelChoiceField(queryset=Customer.objects.filter(is_active=True), required=False, empty_label="Tous les clients", widget=forms.Select(attrs={'class': 'form-control'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    payment_method = forms.ChoiceField(choices=[('', 'Tous les modes')] + Sale.PAYMENT_METHODS, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    is_finalized = forms.ChoiceField(choices=[('', 'Tous'), ('true', 'Finalisées seulement'), ('false', 'Brouillons seulement')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))


class QuickSaleForm(forms.ModelForm):
    """Simplified form for quick sales"""
    class Meta:
        model = Sale
        fields = ['vehicle', 'customer', 'sale_price', 'payment_method']
        widgets = {'sale_price': forms.NumberInput(attrs={'step': '0.01'})}
```

---

# Suppliers App

## suppliers/forms.py

```
python
from django import forms
from .models import Supplier
from core.models import Currency

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'country', 'contact_person', 'phone', 'email', 'address', 'currency', 'payment_terms', 'notes', 'is_active']
        widgets = {'address': forms.Textarea(attrs={'rows': 3}), 'notes': forms.Textarea(attrs={'rows': 3}), 'payment_terms': forms.TextInput(attrs={'placeholder': 'ex: 30% avance, 70% à la livraison'})}


class SupplierSearchForm(forms.Form):
    """Form for searching and filtering suppliers"""
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Rechercher par nom, contact, email...', 'class': 'form-control'}))
    country = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    currency = forms.ModelChoiceField(queryset=Currency.objects.filter(is_active=True), required=False, empty_label="Toutes les devises", widget=forms.Select(attrs={'class': 'form-control'}))
    is_active = forms.ChoiceField(choices=[('', 'Tous'), ('true', 'Actifs seulement'), ('false', 'Inactifs seulement')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
```

---

# System Settings App

## system_settings/forms.py

```
python
from django import forms
from .models import SystemConfiguration, ExchangeRateHistory, TaxRateHistory, UserPreference, SystemLog
from core.models import Currency

class SystemConfigurationForm(forms.ModelForm):
    class Meta:
        model = SystemConfiguration
        fields = ["company_name", "company_nif", "company_address", "company_phone", "company_email", "default_tva_rate", "default_tariff_rate", "default_commission_rate", "reservation_duration_days", "invoice_due_days", "enable_email_notifications", "enable_overdue_alerts", "overdue_alert_days"]
        widgets = {"company_address": forms.Textarea(attrs={"rows": 3}), "default_tva_rate": forms.NumberInput(attrs={"step": "0.01"}), "default_tariff_rate": forms.NumberInput(attrs={"step": "0.01"}), "default_commission_rate": forms.NumberInput(attrs={"step": "0.01"})}


class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRateHistory
        fields = ["from_currency", "to_currency", "rate", "effective_date", "source", "notes"]
        widgets = {"effective_date": forms.DateInput(attrs={"type": "date"}), "rate": forms.NumberInput(attrs={"step": "0.000001"}), "notes": forms.Textarea(attrs={"rows": 3})}


class TaxRateForm(forms.ModelForm):
    class Meta:
        model = TaxRateHistory
        fields = ["tax_type", "rate", "effective_date", "description"]
        widgets = {"effective_date": forms.DateInput(attrs={"type": "date"}), "rate": forms.NumberInput(attrs={"step": "0.01"})}


class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ["theme", "language", "default_page_size", "email_notifications", "browser_notifications", "default_export_format"]


class ExchangeRateSearchForm(forms.Form):
    """Form for searching exchange rates"""
    from_currency = forms.ModelChoiceField(queryset=Currency.objects.filter(is_active=True), required=False, empty_label="Toutes les devises source", widget=forms.Select(attrs={"class": "form-control"}))
    to_currency = forms.ModelChoiceField(queryset=Currency.objects.filter(is_active=True), required=False, empty_label="Toutes les devises cible", widget=forms.Select(attrs={"class": "form-control"}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))


class SystemLogFilterForm(forms.Form):
    """Form for filtering system logs"""
    level = forms.ChoiceField(choices=[("", "Tous les niveaux")] + SystemLog.LOG_LEVELS, required=False, widget=forms.Select(attrs={"class": "form-control"}))
    action_type = forms.ChoiceField(choices=[("", "Toutes les actions")] + SystemLog.ACTION_TYPES, required=False, widget=forms.Select(attrs={"class": "form-control"}))
    user = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"placeholder": "Nom d'utilisateur", "class": "form-control"}))
    date_from = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}))
    date_to = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}))
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={"placeholder": "Rechercher dans les messages...", "class": "form-control"}))
```
