# Django Views Compilation

This document contains all views from all Django apps in the project.

---

# Customers App

## customers/views.py

```
python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Max
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Customer, CustomerNote
from .forms import CustomerForm, CustomerSearchForm, CustomerNoteForm, QuickCustomerForm
from core.decorators import trader_required


@login_required
def customer_list(request):
    """List all customers with search and filter capabilities"""
    customers = Customer.objects.all()
    search_form = CustomerSearchForm(request.GET)
    if search_form.is_valid():
        search = search_form.cleaned_data.get("search")
        if search:
            customers = customers.filter(
                Q(name__icontains=search) | Q(phone__icontains=search) |
                Q(email__icontains=search) | Q(nif_tax_id__icontains=search)
            )
        customer_type = search_form.cleaned_data.get("customer_type")
        if customer_type:
            customers = customers.filter(customer_type=customer_type)
        wilaya = search_form.cleaned_data.get("wilaya")
        if wilaya:
            customers = customers.filter(wilaya=wilaya)
        is_active = search_form.cleaned_data.get("is_active")
        if is_active == "true":
            customers = customers.filter(is_active=True)
        elif is_active == "false":
            customers = customers.filter(is_active=False)
        has_outstanding = search_form.cleaned_data.get("has_outstanding")
        if has_outstanding:
            customers = customers.filter(invoice__balance_due__gt=0).distinct()
    customers = customers.annotate(
        sales_count=Count("sale"), purchases_total=Sum("sale__sale_price"), last_sale_date=Max("sale__sale_date")
    )
    paginator = Paginator(customers, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "search_form": search_form, "total_count": customers.count()}
    return render(request, "customers/list.html", context)


@trader_required
def customer_create(request):
    """Create new customer"""
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            messages.success(request, f"Client '{customer.name}' créé avec succès.")
            return redirect("customers:detail", pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, "customers/form.html", {"form": form, "title": "Nouveau Client"})


@login_required
def customer_detail(request, pk):
    """Customer detail view with purchase history"""
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sale_set.all().select_related("vehicle", "assigned_trader")
    invoices = customer.invoice_set.all().order_by("-invoice_date")
    outstanding_invoices = invoices.filter(balance_due__gt=0)
    total_purchases = sales.count()
    total_value = sum(sale.sale_price for sale in sales)
    total_outstanding = sum(invoice.balance_due for invoice in outstanding_invoices)
    recent_sales = sales.order_by("-sale_date")[:5]
    recent_notes = customer.customer_notes.order_by("-created_at")[:5]
    note_form = CustomerNoteForm()
    context = {
        "customer": customer, "total_purchases": total_purchases, "total_value": total_value,
        "total_outstanding": total_outstanding, "recent_sales": recent_sales, "recent_notes": recent_notes,
        "outstanding_invoices": outstanding_invoices, "note_form": note_form,
    }
    return render(request, "customers/detail.html", context)


@trader_required
def customer_edit(request, pk):
    """Edit customer"""
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.updated_by = request.user
            customer.save()
            messages.success(request, f"Client '{customer.name}' modifié avec succès.")
            return redirect("customers:detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, "customers/form.html", {"form": form, "customer": customer, "title": f"Modifier {customer.name}"})


@login_required
def customer_add_note(request, pk):
    """Add note to customer"""
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.customer = customer
            note.created_by = request.user
            note.save()
            messages.success(request, "Note ajoutée avec succès.")
            return redirect("customers:detail", pk=pk)
    return redirect("customers:detail", pk=pk)


@login_required
def customer_ajax_search(request):
    """AJAX endpoint for customer search in dropdowns"""
    term = request.GET.get("term", "")
    customers = Customer.objects.filter(is_active=True).filter(
        Q(name__icontains=term) | Q(phone__icontains=term)
    )[:10]
    results = [{"id": c.id, "text": f"{c.name} - {c.phone}", "name": c.name, "phone": c.phone,
                "address": c.address, "customer_type": c.customer_type, "nif_tax_id": c.nif_tax_id, "wilaya": c.wilaya}
               for c in customers]
    return JsonResponse({"results": results})


@trader_required
def customer_quick_create(request):
    """Quick customer creation (AJAX)"""
    if request.method == "POST":
        form = QuickCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            return JsonResponse({"success": True, "customer": {"id": customer.id, "name": customer.name,
                        "phone": customer.phone, "address": customer.address, "customer_type": customer.customer_type,
                        "nif_tax_id": customer.nif_tax_id, "wilaya": customer.wilaya}})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    form = QuickCustomerForm()
    return render(request, "customers/quick_form.html", {"form": form})


@trader_required
def customer_toggle_status(request, pk):
    """Toggle customer active status via AJAX"""
    if request.method == "POST":
        customer = get_object_or_404(Customer, pk=pk)
        if customer.is_active and customer.outstanding_balance > 0:
            return JsonResponse({"success": False, "message": "Impossible de désactiver un client avec un solde impayé."})
        customer.is_active = not customer.is_active
        customer.updated_by = request.user
        customer.save()
        status_text = "activé" if customer.is_active else "désactivé"
        return JsonResponse({"success": True, "message": f"Client {status_text} avec succès.", "is_active": customer.is_active})
    return JsonResponse({"success": False, "message": "Méthode non autorisée."})
```

---

# Commissions App

## commissions/views.py

```
python
# Key views from commissions app:
# - my_commission: Trader's own commission view
# - commission_overview: Manager overview of all commissions
# - trader_performance: Trader performance comparison
# - commission_tiers: Manage commission tiers
# - commission_tier_create: Create new commission tier
# - commission_tier_edit: Edit commission tier
# - commission_adjustment_create: Create commission adjustment
# - commission_payment_create: Create commission payment
# - close_commission_period: Close commission period and calculate final commissions
# - approve_commission: Approve commission for payment
# - ajax_commission_calculation: AJAX endpoint for commission calculation preview
```

---

# Core App

## core/views.py

```
python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import datetime, timedelta
from decimal import Decimal
import json


@login_required
def index(request):
    """Index/home view with quick access cards"""
    return render(request, "core/index.html")


@login_required
def dashboard(request):
    """Main dashboard view with comprehensive metrics"""
    # Get user role for customized dashboard
    user_role = None
    if hasattr(request.user, "userprofile"):
        user_role = request.user.userprofile.role

    # Date ranges
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    twelve_months_ago = today - timedelta(days=365)

    # Import models
    from inventory.models import Vehicle, StockAlert
    from sales.models import Sale, Invoice
    from purchases.models import Purchase
    from payments.models import Payment
    from customers.models import Customer
    from commissions.models import CommissionSummary
    from django.contrib.auth.models import User

    # INVENTORY METRICS
    available_vehicles = Vehicle.objects.filter(status="available")
    total_inventory_value = sum(v.landed_cost or 0 for v in available_vehicles)
    vehicles_in_stock = available_vehicles.count()
    vehicles_reserved = Vehicle.objects.filter(status="reserved").count()
    vehicles_in_customs = Vehicle.objects.filter(status="at_customs").count()
    vehicles_in_transit = Vehicle.objects.filter(status="in_transit").count()

    # SALES METRICS
    current_month_sales = Sale.objects.filter(sale_date__gte=current_month_start, sale_date__lte=today, is_finalized=True)
    last_month_sales = Sale.objects.filter(sale_date__gte=last_month_start, sale_date__lte=last_month_end, is_finalized=True)
    monthly_sales_count = current_month_sales.count()
    monthly_revenue = sum(s.sale_price for s in current_month_sales)
    monthly_margin = sum(s.margin_amount for s in current_month_sales)
    last_month_revenue = sum(s.sale_price for s in last_month_sales)
    revenue_change_pct = ((monthly_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
    margin_percentage = (monthly_margin / monthly_revenue * 100) if monthly_revenue > 0 else 0

    # PAYMENT METRICS
    outstanding_invoices = Invoice.objects.filter(balance_due__gt=0)
    total_outstanding = sum(inv.balance_due for inv in outstanding_invoices)
    outstanding_count = outstanding_invoices.count()
    overdue_invoices = outstanding_invoices.filter(due_date__lt=today, status="issued").count()

    # STOCK ALERTS
    stock_alerts = StockAlert.objects.filter(is_resolved=False).order_by("-created_at")[:5]
    alerts_list = []
    for alert in stock_alerts:
        priority = "high" if alert.alert_type in ["slow_moving", "customs_delayed"] else "medium"
        alerts_list.append({"priority": priority, "type": alert.get_alert_type_display(), "message": alert.message,
                          "vehicle": alert.vehicle, "created": alert.created_at})

    # Context data
    context = {
        "user_role": user_role, "current_date": today,
        "total_inventory_value": total_inventory_value, "vehicles_in_stock": vehicles_in_stock,
        "vehicles_reserved": vehicles_reserved, "vehicles_in_customs": vehicles_in_customs,
        "vehicles_in_transit": vehicles_in_transit,
        "monthly_sales_count": monthly_sales_count, "monthly_revenue": monthly_revenue,
        "revenue_change_pct": revenue_change_pct, "monthly_margin": monthly_margin,
        "margin_percentage": margin_percentage,
        "outstanding_count": outstanding_count, "total_outstanding": total_outstanding,
        "overdue_count": overdue_invoices,
        "alerts_list": sorted(alerts_list, key=lambda x: (0 if x["priority"] == "high" else 1, x["created"]), reverse=True)[:6],
    }
    return render(request, "core/dashboard.html", context)
```

---

# Inventory App

## inventory/views.py

```
python
# Key views from inventory app:
# - vehicle_list: List all vehicles with search and filter
# - vehicle_detail: Vehicle detail view
# - vehicle_create: Create new vehicle record
# - vehicle_edit: Edit vehicle details
# - vehicle_reserve: Reserve vehicle for trader
# - vehicle_release_reservation: Release vehicle reservation
# - vehicle_add_photo: Add photo to vehicle
# - stock_alerts: View stock alerts
# - resolve_alert: Resolve stock alert
# - generate_automatic_alerts: Generate automatic stock alerts
```

---

# Payments App

## payments/views.py

```
python
# Key views from payments app:
# - payment_list: List all payments with search and filter
# - payment_create: Create new payment
# - payment_detail: Payment detail view
# - payment_edit: Edit payment
# - outstanding_invoices: Outstanding invoices report
# - quick_payment: Quick payment entry for specific invoice
# - payment_reminder_create: Create payment reminder
# - payment_plan_create: Create payment plan
# - payment_plan_detail: Payment plan detail with installments
# - installment_payment: Record payment for specific installment
# - ajax_invoice_balance: AJAX endpoint to get invoice balance
```

---

# Purchases App

## purchases/views.py

```
python
# Key views from purchases app:
# - purchase_list: List all purchases with search and filter
# - purchase_create: Create new vehicle purchase
# - purchase_detail: Purchase detail view with all costs
# - purchase_add_freight: Add freight costs to purchase
# - purchase_add_customs: Add customs declaration and duties
# - purchase_edit_freight: Edit freight costs
# - purchase_edit_customs: Edit customs declaration
# - ajax_calculate_customs: AJAX endpoint to calculate customs duties
# - customs_mark_cleared: Mark customs as cleared via AJAX
```

---

# Reports App

## reports/views.py

```
python
# Key views from reports app:
# - dashboard: Reports dashboard with quick links
# - profit_analysis: Profit analysis report
# - inventory_status: Inventory status report
# - sales_summary: Sales summary report
# - payment_status: Payment status report
# - export_report: Export report data
# - ajax_chart_data: AJAX endpoint for chart data
```

---

# Sales App

## sales/views.py

```
python
# Key views from sales app:
# - sale_list: List all sales with search and filter
# - sale_create: Create new sale
# - sale_detail: Sale detail view
# - sale_edit: Edit sale
# - sale_create_invoice: Create invoice for sale
# - invoice_detail: Invoice detail view
# - invoice_print: Print-ready invoice view
# - sale_finalize: Finalize sale
# - ajax_vehicle_details: AJAX endpoint to get vehicle details
# - ajax_calculate_margin: AJAX endpoint to calculate sale margin
# - quick_sale: Quick sale creation
```

---

# Suppliers App

## suppliers/views.py

```
python
# Key views from suppliers app:
# - supplier_list: List all suppliers with search and filter
# - supplier_create: Create new supplier
# - supplier_detail: Supplier detail view with purchase history
# - supplier_edit: Edit supplier
# - supplier_toggle_status: Toggle supplier active status
# - supplier_ajax_search: AJAX endpoint for supplier search
```

---

# System Settings App

## system_settings/views.py

```
python
# Key views from system_settings app:
# - system_configuration: System configuration management
# - exchange_rates: Exchange rates management
# - exchange_rate_create: Create new exchange rate
# - exchange_rate_edit: Edit exchange rate
# - tax_rates: Tax rates management
# - tax_rate_create: Create new tax rate
# - tax_rate_edit: Edit tax rate
# - user_preferences: User preferences management
# - system_logs: System logs viewer
# - clear_old_logs: Clear old system logs
# - ajax_latest_exchange_rate: AJAX endpoint to get latest exchange rate
# - system_status: System status dashboard
```
