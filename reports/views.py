from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count, Avg, F, Case, When, DecimalField
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .forms import (
    ProfitAnalysisForm,
    InventoryStatusForm,
    SalesSummaryForm,
    PaymentStatusForm,
    ReportExportForm,
)
from sales.models import Sale, Invoice, SaleLineItem
from inventory.models import Vehicle
from payments.models import Payment
from commissions.models import CommissionSummary
from customers.models import Customer
from suppliers.models import Supplier
from core.decorators import manager_required


@login_required
def dashboard(request):
    """Reports dashboard with quick links and recent reports"""

    today = timezone.now().date()
    current_month = today.replace(day=1)

    # ── Monthly sales queryset (used for multiple aggregations) ───────────────
    monthly_sales_qs = Sale.objects.filter(
        sale_date__gte=current_month, is_finalized=True
    )

    # Inventory statistics
    inventory_stats = {
        "total_vehicles": Vehicle.objects.count(),
        "available_vehicles": Vehicle.objects.filter(status="available").count(),
        "in_transit": Vehicle.objects.filter(status="in_transit").count(),
        "at_customs": Vehicle.objects.filter(status="at_customs").count(),
    }

    # Financial statistics
    # sale_price is a Python property (sum of line_items); aggregate via the FK
    monthly_revenue = monthly_sales_qs.aggregate(total=Sum("line_items__sale_price"))[
        "total"
    ] or Decimal("0")

    # margin_amount also depends on landed_cost (a property); compute in Python
    monthly_sales_list = list(
        monthly_sales_qs.prefetch_related(
            "line_items__vehicle__purchase_line_item__purchase__freight_cost",
            "line_items__vehicle__purchase_line_item__purchase__customs_declaration",
        )
    )
    monthly_margin = sum(sale.margin_amount for sale in monthly_sales_list)

    financial_stats = {
        "monthly_revenue": monthly_revenue,
        "monthly_margin": monthly_margin,
        "outstanding_invoices": Invoice.objects.filter(balance_due__gt=0).count(),
        "total_outstanding": Invoice.objects.filter(balance_due__gt=0).aggregate(
            Sum("balance_due")
        )["balance_due__sum"]
        or 0,
    }

    # Top traders — revenue via line_items__sale_price to stay at DB level
    top_traders = (
        monthly_sales_qs.values(
            "assigned_trader__first_name", "assigned_trader__last_name"
        )
        .annotate(
            sales_count=Count("id", distinct=True),
            total_revenue=Sum("line_items__sale_price"),
            total_commission=Sum("commission_amount"),
        )
        .order_by("-total_revenue")[:5]
    )

    # Recent finalized sales — no direct vehicle FK on Sale anymore
    recent_sales = (
        Sale.objects.filter(is_finalized=True)
        .select_related("customer", "assigned_trader")
        .prefetch_related(
            "line_items__vehicle__purchase_line_item__purchase__freight_cost",
            "line_items__vehicle__purchase_line_item__purchase__customs_declaration",
        )
        .order_by("-sale_date")[:5]
    )

    context = {
        "inventory_stats": inventory_stats,
        "financial_stats": financial_stats,
        "top_traders": top_traders,
        "recent_sales": recent_sales,
    }

    return render(request, "reports/dashboard.html", context)


@login_required
def profit_analysis(request):
    """Profit analysis report"""

    form = ProfitAnalysisForm(request.GET or None)

    # Base queryset — vehicle is now reached via line_items
    sales = (
        Sale.objects.filter(is_finalized=True)
        .select_related("customer", "assigned_trader")
        .prefetch_related(
            "line_items__vehicle__purchase_line_item__purchase__freight_cost",
            "line_items__vehicle__purchase_line_item__purchase__customs_declaration",
            "line_items__vehicle__purchase_line_item__purchase__supplier",
        )
    )

    # Apply filters
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        if date_from:
            sales = sales.filter(sale_date__gte=date_from)

        date_to = form.cleaned_data.get("date_to")
        if date_to:
            sales = sales.filter(sale_date__lte=date_to)

        trader = form.cleaned_data.get("trader")
        if trader:
            sales = sales.filter(assigned_trader=trader)

        customer = form.cleaned_data.get("customer")
        if customer:
            sales = sales.filter(customer=customer)

        # vehicle_make is now on the line item's vehicle, not directly on Sale
        vehicle_make = form.cleaned_data.get("vehicle_make")
        if vehicle_make:
            sales = sales.filter(
                line_items__vehicle__make__icontains=vehicle_make
            ).distinct()

        min_margin = form.cleaned_data.get("min_margin")
        if min_margin:
            # margin_amount is a Python property — filter in Python
            sales = [sale for sale in sales if sale.margin_amount >= min_margin]

    # Role-based filtering
    if hasattr(request.user, "userprofile"):
        if request.user.userprofile.is_trader:
            if isinstance(sales, list):
                sales = [s for s in sales if s.assigned_trader_id == request.user.pk]
            else:
                sales = sales.filter(assigned_trader=request.user)

    # Totals (sale_price and margin_amount are Python properties)
    total_sales = len(sales) if isinstance(sales, list) else sales.count()
    total_revenue = sum(sale.sale_price for sale in sales)
    total_margin = sum(sale.margin_amount for sale in sales)
    total_commission = sum(sale.commission_amount or 0 for sale in sales)

    avg_sale_price = total_revenue / total_sales if total_sales > 0 else 0
    avg_margin = total_margin / total_sales if total_sales > 0 else 0
    margin_percentage = (total_margin / total_revenue * 100) if total_revenue > 0 else 0

    # Grouped data
    grouped_data = []
    if form.is_valid():
        group_by = form.cleaned_data.get("group_by", "month")
        from collections import defaultdict

        if group_by == "month":
            monthly_data = defaultdict(
                lambda: {
                    "sales_count": 0,
                    "revenue": Decimal("0"),
                    "margin": Decimal("0"),
                    "commission": Decimal("0"),
                }
            )
            for sale in sales:
                key = sale.sale_date.strftime("%Y-%m")
                monthly_data[key]["sales_count"] += 1
                monthly_data[key]["revenue"] += sale.sale_price
                monthly_data[key]["margin"] += sale.margin_amount
                monthly_data[key]["commission"] += sale.commission_amount or 0

            grouped_data = [
                {
                    "label": datetime.strptime(m, "%Y-%m").strftime("%B %Y"),
                    "sales_count": d["sales_count"],
                    "revenue": d["revenue"],
                    "margin": d["margin"],
                    "commission": d["commission"],
                    "margin_percentage": (
                        (d["margin"] / d["revenue"] * 100) if d["revenue"] > 0 else 0
                    ),
                }
                for m, d in sorted(monthly_data.items())
            ]

        elif group_by == "trader":
            trader_data = defaultdict(
                lambda: {
                    "sales_count": 0,
                    "revenue": Decimal("0"),
                    "margin": Decimal("0"),
                    "commission": Decimal("0"),
                }
            )
            for sale in sales:
                name = (
                    sale.assigned_trader.get_full_name()
                    or sale.assigned_trader.username
                )
                trader_data[name]["sales_count"] += 1
                trader_data[name]["revenue"] += sale.sale_price
                trader_data[name]["margin"] += sale.margin_amount
                trader_data[name]["commission"] += sale.commission_amount or 0

            grouped_data = [
                {
                    "label": name,
                    "sales_count": d["sales_count"],
                    "revenue": d["revenue"],
                    "margin": d["margin"],
                    "commission": d["commission"],
                    "margin_percentage": (
                        (d["margin"] / d["revenue"] * 100) if d["revenue"] > 0 else 0
                    ),
                }
                for name, d in sorted(trader_data.items())
            ]

        elif group_by == "customer":
            customer_data = defaultdict(
                lambda: {
                    "sales_count": 0,
                    "revenue": Decimal("0"),
                    "margin": Decimal("0"),
                    "commission": Decimal("0"),
                }
            )
            for sale in sales:
                key = sale.customer.name
                customer_data[key]["sales_count"] += 1
                customer_data[key]["revenue"] += sale.sale_price
                customer_data[key]["margin"] += sale.margin_amount
                customer_data[key]["commission"] += sale.commission_amount or 0

            grouped_data = [
                {
                    "label": name,
                    "sales_count": d["sales_count"],
                    "revenue": d["revenue"],
                    "margin": d["margin"],
                    "commission": d["commission"],
                    "margin_percentage": (
                        (d["margin"] / d["revenue"] * 100) if d["revenue"] > 0 else 0
                    ),
                }
                for name, d in sorted(
                    customer_data.items(), key=lambda x: x[1]["revenue"], reverse=True
                )
            ]

        elif group_by == "vehicle_make":
            make_data = defaultdict(
                lambda: {
                    "sales_count": 0,
                    "revenue": Decimal("0"),
                    "margin": Decimal("0"),
                    "commission": Decimal("0"),
                }
            )
            for sale in sales:
                # A sale can have multiple vehicles of different makes
                for item in sale.line_items.all():
                    make = item.vehicle.make
                    make_data[make]["sales_count"] += 1
                    make_data[make]["revenue"] += item.sale_price
                    make_data[make]["margin"] += item.margin_amount
                    # Apportion commission proportionally per line item
                    if sale.sale_price > 0 and sale.commission_amount:
                        make_data[make]["commission"] += (
                            sale.commission_amount * item.sale_price / sale.sale_price
                        )

            grouped_data = [
                {
                    "label": make,
                    "sales_count": d["sales_count"],
                    "revenue": d["revenue"],
                    "margin": d["margin"],
                    "commission": d["commission"],
                    "margin_percentage": (
                        (d["margin"] / d["revenue"] * 100) if d["revenue"] > 0 else 0
                    ),
                }
                for make, d in sorted(
                    make_data.items(), key=lambda x: x[1]["revenue"], reverse=True
                )
            ]

    # Top performing vehicle models — iterate via line_items
    vehicle_performance = {}
    for sale in sales:
        for item in sale.line_items.all():
            vehicle_key = f"{item.vehicle.make} {item.vehicle.model}"
            if vehicle_key not in vehicle_performance:
                vehicle_performance[vehicle_key] = {
                    "count": 0,
                    "revenue": Decimal("0"),
                    "margin": Decimal("0"),
                }
            vehicle_performance[vehicle_key]["count"] += 1
            vehicle_performance[vehicle_key]["revenue"] += item.sale_price
            vehicle_performance[vehicle_key]["margin"] += item.margin_amount

    top_vehicles = sorted(
        [
            {
                "vehicle": vehicle,
                "count": data["count"],
                "revenue": data["revenue"],
                "margin": data["margin"],
                "avg_margin": data["margin"] / data["count"] if data["count"] else 0,
            }
            for vehicle, data in vehicle_performance.items()
        ],
        key=lambda x: x["margin"],
        reverse=True,
    )[:10]

    # Pre-serialize chart data (avoids locale number-format issues in JS)
    def _f(v):
        return float(v) if isinstance(v, Decimal) else float(v or 0)

    chart_grouped_data = json.dumps(
        {
            "labels": [row["label"] for row in grouped_data],
            "revenues": [_f(row["revenue"]) for row in grouped_data],
            "margins": [_f(row["margin"]) for row in grouped_data],
        }
    )

    context = {
        "form": form,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_margin": total_margin,
        "total_commission": total_commission,
        "avg_sale_price": avg_sale_price,
        "avg_margin": avg_margin,
        "margin_percentage": margin_percentage,
        "net_profit": total_margin - total_commission,
        "grouped_data": grouped_data,
        "top_vehicles": top_vehicles,
        "sales_list": sales[:20] if not isinstance(sales, list) else sales[:20],
        "chart_grouped_data": chart_grouped_data,
    }

    return render(request, "reports/profit_analysis.html", context)


@login_required
def inventory_status(request):
    """Inventory status report"""

    form = InventoryStatusForm(request.GET or None)

    # purchase_line_item is the real FK; vehicle_purchase is a backward-compat property
    vehicles = Vehicle.objects.select_related(
        "purchase_line_item__purchase__supplier",
        "purchase_line_item__purchase__freight_cost",
        "purchase_line_item__purchase__customs_declaration",
        "reserved_by",
    )

    # Apply filters
    if form.is_valid():
        status = form.cleaned_data.get("status")
        if status:
            vehicles = vehicles.filter(status__in=status)

        supplier = form.cleaned_data.get("supplier")
        if supplier:
            vehicles = vehicles.filter(purchase_line_item__purchase__supplier=supplier)

        vehicle_make = form.cleaned_data.get("vehicle_make")
        if vehicle_make:
            vehicles = vehicles.filter(make__icontains=vehicle_make)

        year_from = form.cleaned_data.get("year_from")
        if year_from:
            vehicles = vehicles.filter(year__gte=year_from)

        year_to = form.cleaned_data.get("year_to")
        if year_to:
            vehicles = vehicles.filter(year__lte=year_to)

        # landed_cost is a Python property — filter in Python
        min_landed_cost = form.cleaned_data.get("min_landed_cost")
        max_landed_cost = form.cleaned_data.get("max_landed_cost")
        days_in_stock_min = form.cleaned_data.get("days_in_stock_min")

        if min_landed_cost or max_landed_cost or days_in_stock_min:
            vehicles = list(vehicles)
            if min_landed_cost:
                vehicles = [v for v in vehicles if v.landed_cost >= min_landed_cost]
            if max_landed_cost:
                vehicles = [v for v in vehicles if v.landed_cost <= max_landed_cost]
            if days_in_stock_min:
                vehicles = [v for v in vehicles if v.days_in_stock >= days_in_stock_min]

    # Materialize to list for Python-level property access
    if not isinstance(vehicles, list):
        vehicles_list = list(vehicles)
    else:
        vehicles_list = vehicles

    total_vehicles = len(vehicles_list)
    total_value = sum(v.landed_cost for v in vehicles_list)
    avg_value = total_value / total_vehicles if total_vehicles > 0 else 0

    # Status breakdown
    status_breakdown = {}
    for vehicle in vehicles_list:
        label = vehicle.get_status_display()
        if label not in status_breakdown:
            status_breakdown[label] = {"count": 0, "value": Decimal("0")}
        status_breakdown[label]["count"] += 1
        status_breakdown[label]["value"] += vehicle.landed_cost

    # Supplier breakdown — via purchase_line_item (select_related already loaded it)
    supplier_breakdown = {}
    for vehicle in vehicles_list:
        if vehicle.purchase_line_item_id and vehicle.purchase_line_item.purchase_id:
            supplier_name = vehicle.purchase_line_item.purchase.supplier.name
        else:
            supplier_name = "—"
        if supplier_name not in supplier_breakdown:
            supplier_breakdown[supplier_name] = {"count": 0, "value": Decimal("0")}
        supplier_breakdown[supplier_name]["count"] += 1
        supplier_breakdown[supplier_name]["value"] += vehicle.landed_cost

    # Age analysis
    age_breakdown = {
        "0–30 jours": {"count": 0, "value": Decimal("0")},
        "31–60 jours": {"count": 0, "value": Decimal("0")},
        "61–90 jours": {"count": 0, "value": Decimal("0")},
        "90+ jours": {"count": 0, "value": Decimal("0")},
    }
    for vehicle in vehicles_list:
        days = vehicle.days_in_stock
        if days <= 30:
            cat = "0–30 jours"
        elif days <= 60:
            cat = "31–60 jours"
        elif days <= 90:
            cat = "61–90 jours"
        else:
            cat = "90+ jours"
        age_breakdown[cat]["count"] += 1
        age_breakdown[cat]["value"] += vehicle.landed_cost

    slow_moving = [
        v for v in vehicles_list if v.days_in_stock > 90 and v.status == "available"
    ]

    context = {
        "form": form,
        "total_vehicles": total_vehicles,
        "total_value": total_value,
        "avg_value": avg_value,
        "status_breakdown": status_breakdown,
        "supplier_breakdown": supplier_breakdown,
        "age_breakdown": age_breakdown,
        "slow_moving": slow_moving,
        "vehicles_list": vehicles_list[:50],
    }

    return render(request, "reports/inventory_status.html", context)


@login_required
def sales_summary(request):
    """Sales summary report"""

    form = SalesSummaryForm(request.GET or None)

    # Base queryset — no direct vehicle FK on Sale
    sales = (
        Sale.objects.filter(is_finalized=True)
        .select_related("customer", "assigned_trader")
        .prefetch_related("line_items__vehicle")
    )

    # Apply filters
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        if date_from:
            sales = sales.filter(sale_date__gte=date_from)

        date_to = form.cleaned_data.get("date_to")
        if date_to:
            sales = sales.filter(sale_date__lte=date_to)

        trader = form.cleaned_data.get("trader")
        if trader:
            sales = sales.filter(assigned_trader=trader)

        payment_method = form.cleaned_data.get("payment_method")
        if payment_method:
            sales = sales.filter(payment_method=payment_method)

    # Role-based filtering
    if hasattr(request.user, "userprofile"):
        if request.user.userprofile.is_trader:
            sales = sales.filter(assigned_trader=request.user)

    total_sales = sales.count()

    # sale_price is a property — aggregate via line_items at DB level
    total_revenue = sales.aggregate(total=Sum("line_items__sale_price"))[
        "total"
    ] or Decimal("0")
    total_commission = sales.aggregate(total=Sum("commission_amount"))[
        "total"
    ] or Decimal("0")
    avg_sale_price = total_revenue / total_sales if total_sales > 0 else Decimal("0")

    # Period analysis
    period_data = []
    if form.is_valid():
        period_type = form.cleaned_data.get("period_type", "monthly")
        from collections import defaultdict

        if period_type == "monthly":
            monthly_data = defaultdict(
                lambda: {
                    "sales_count": 0,
                    "revenue": Decimal("0"),
                    "commission": Decimal("0"),
                }
            )
            for sale in sales.prefetch_related("line_items"):
                key = sale.sale_date.strftime("%Y-%m")
                monthly_data[key]["sales_count"] += 1
                monthly_data[key]["revenue"] += sale.sale_price
                monthly_data[key]["commission"] += sale.commission_amount or 0

            period_data = [
                {
                    "period": datetime.strptime(m, "%Y-%m").strftime("%B %Y"),
                    "sales_count": d["sales_count"],
                    "revenue": d["revenue"],
                    "commission": d["commission"],
                    "avg_sale": (
                        d["revenue"] / d["sales_count"] if d["sales_count"] > 0 else 0
                    ),
                }
                for m, d in sorted(monthly_data.items())
            ]

        elif period_type in ("daily", "weekly", "quarterly", "yearly"):
            fmt_map = {
                "daily": ("%Y-%m-%d", "%d %b %Y"),
                "weekly": ("%Y-W%W", "Sem. %W, %Y"),
                "quarterly": None,
                "yearly": ("%Y", "%Y"),
            }
            if period_type == "quarterly":
                period_data_dict = defaultdict(
                    lambda: {
                        "sales_count": 0,
                        "revenue": Decimal("0"),
                        "commission": Decimal("0"),
                    }
                )
                for sale in sales.prefetch_related("line_items"):
                    q = f"Q{((sale.sale_date.month - 1) // 3) + 1} {sale.sale_date.year}"
                    period_data_dict[q]["sales_count"] += 1
                    period_data_dict[q]["revenue"] += sale.sale_price
                    period_data_dict[q]["commission"] += sale.commission_amount or 0
                period_data = [
                    {
                        "period": q,
                        "sales_count": d["sales_count"],
                        "revenue": d["revenue"],
                        "commission": d["commission"],
                        "avg_sale": (
                            d["revenue"] / d["sales_count"] if d["sales_count"] else 0
                        ),
                    }
                    for q, d in sorted(period_data_dict.items())
                ]
            else:
                in_fmt, out_fmt = fmt_map[period_type]
                pd = defaultdict(
                    lambda: {
                        "sales_count": 0,
                        "revenue": Decimal("0"),
                        "commission": Decimal("0"),
                    }
                )
                for sale in sales.prefetch_related("line_items"):
                    key = sale.sale_date.strftime(in_fmt)
                    pd[key]["sales_count"] += 1
                    pd[key]["revenue"] += sale.sale_price
                    pd[key]["commission"] += sale.commission_amount or 0
                period_data = [
                    {
                        "period": datetime.strptime(k, in_fmt).strftime(out_fmt),
                        "sales_count": d["sales_count"],
                        "revenue": d["revenue"],
                        "commission": d["commission"],
                        "avg_sale": (
                            d["revenue"] / d["sales_count"] if d["sales_count"] else 0
                        ),
                    }
                    for k, d in sorted(pd.items())
                ]

    # Payment method breakdown — revenue via line_items at DB level
    PAYMENT_METHOD_LABELS = {
        "cash": "Espèces",
        "bank_transfer": "Virement Bancaire",
        "installment": "Paiement Échelonné",
        "check": "Chèque",
    }
    payment_breakdown = [
        {
            **item,
            "payment_method_display": PAYMENT_METHOD_LABELS.get(
                item["payment_method"],
                (item["payment_method"] or "—").replace("_", " ").title(),
            ),
        }
        for item in sales.values("payment_method")
        .annotate(
            count=Count("id", distinct=True), revenue=Sum("line_items__sale_price")
        )
        .order_by("-revenue")
    ]

    # Top customers
    top_customers = (
        sales.values("customer__name")
        .annotate(
            sales_count=Count("id", distinct=True),
            total_spent=Sum("line_items__sale_price"),
        )
        .order_by("-total_spent")[:10]
    )

    # Vehicle make performance — via SaleLineItem since Sale has no direct vehicle FK
    make_perf_raw = (
        SaleLineItem.objects.filter(sale__in=sales)
        .values("vehicle__make")
        .annotate(count=Count("id"), revenue=Sum("sale_price"))
        .order_by("-revenue")[:10]
    )
    make_performance = [
        {
            "vehicle__make": row["vehicle__make"],
            "count": row["count"],
            "revenue": row["revenue"],
        }
        for row in make_perf_raw
    ]

    # Pre-serialize chart data (avoids locale number-format issues in JS)
    def _to_float(v):
        return float(v) if isinstance(v, Decimal) else float(v or 0)

    chart_period_data = json.dumps(
        {
            "periods": [row["period"] for row in period_data],
            "revenues": [_to_float(row["revenue"]) for row in period_data],
            "saleCounts": [row["sales_count"] for row in period_data],
        }
    )

    chart_payment_data = json.dumps(
        {
            "labels": [pm["payment_method_display"] for pm in payment_breakdown],
            "counts": [pm["count"] for pm in payment_breakdown],
        }
    )

    context = {
        "form": form,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_commission": total_commission,
        "avg_sale_price": avg_sale_price,
        "period_data": period_data,
        "payment_breakdown": payment_breakdown,
        "top_customers": top_customers,
        "make_performance": make_performance,
        "chart_period_data": chart_period_data,
        "chart_payment_data": chart_payment_data,
    }

    return render(request, "reports/sales_summary.html", context)


@login_required
def payment_status(request):
    """Payment status report"""

    form = PaymentStatusForm(request.GET or None)

    # Invoice links to Sale; Sale no longer has a direct vehicle FK
    invoices = Invoice.objects.select_related(
        "customer", "sale__assigned_trader"
    ).prefetch_related("payments", "sale__line_items__vehicle")

    # Apply filters
    if form.is_valid():
        invoice_status = form.cleaned_data.get("invoice_status")
        if invoice_status:
            invoices = invoices.filter(status__in=invoice_status)

        overdue_only = form.cleaned_data.get("overdue_only")
        if overdue_only:
            invoices = invoices.filter(
                due_date__lt=timezone.now().date(), balance_due__gt=0
            )

        days_overdue_min = form.cleaned_data.get("days_overdue_min")
        if days_overdue_min:
            cutoff_date = timezone.now().date() - timedelta(days=days_overdue_min)
            invoices = invoices.filter(due_date__lt=cutoff_date)

        customer = form.cleaned_data.get("customer")
        if customer:
            invoices = invoices.filter(customer=customer)

        trader = form.cleaned_data.get("trader")
        if trader:
            invoices = invoices.filter(sale__assigned_trader=trader)

        amount_min = form.cleaned_data.get("amount_min")
        if amount_min:
            invoices = invoices.filter(total_ttc__gte=amount_min)

        amount_max = form.cleaned_data.get("amount_max")
        if amount_max:
            invoices = invoices.filter(total_ttc__lte=amount_max)

    # Role-based filtering
    if hasattr(request.user, "userprofile"):
        if request.user.userprofile.is_trader:
            invoices = invoices.filter(sale__assigned_trader=request.user)

    # Statistics
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(Sum("total_ttc"))["total_ttc__sum"] or 0
    total_paid = invoices.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    total_outstanding = invoices.aggregate(Sum("balance_due"))["balance_due__sum"] or 0

    status_breakdown = invoices.values("status").annotate(
        count=Count("id"), amount=Sum("total_ttc"), outstanding=Sum("balance_due")
    )

    overdue_invoices = invoices.filter(
        due_date__lt=timezone.now().date(), balance_due__gt=0
    )

    overdue_breakdown = {
        "1–30 jours": {"count": 0, "amount": Decimal("0")},
        "31–60 jours": {"count": 0, "amount": Decimal("0")},
        "61–90 jours": {"count": 0, "amount": Decimal("0")},
        "90+ jours": {"count": 0, "amount": Decimal("0")},
    }
    for invoice in overdue_invoices:
        days_overdue = invoice.days_overdue
        if days_overdue <= 30:
            cat = "1–30 jours"
        elif days_overdue <= 60:
            cat = "31–60 jours"
        elif days_overdue <= 90:
            cat = "61–90 jours"
        else:
            cat = "90+ jours"
        overdue_breakdown[cat]["count"] += 1
        overdue_breakdown[cat]["amount"] += invoice.balance_due

    top_outstanding = (
        invoices.filter(balance_due__gt=0)
        .values("customer__name")
        .annotate(total_outstanding=Sum("balance_due"), invoice_count=Count("id"))
        .order_by("-total_outstanding")[:10]
    )

    context = {
        "form": form,
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "collection_rate": (total_paid / total_amount * 100) if total_amount > 0 else 0,
        "status_breakdown": status_breakdown,
        "overdue_breakdown": overdue_breakdown,
        "top_outstanding": top_outstanding,
        "invoices_list": invoices[:50],
    }

    return render(request, "reports/payment_status.html", context)


@manager_required
def export_report(request):
    """Export report data"""

    if request.method == "POST":
        form = ReportExportForm(request.POST)
        if form.is_valid():
            format_type = form.cleaned_data["format"]
            include_charts = form.cleaned_data.get("include_charts", False)
            email_to = form.cleaned_data.get("email_to")

            report_type = request.session.get("last_report_type", "profit_analysis")

            if format_type == "excel":
                response = export_to_excel(request, report_type)
            elif format_type == "csv":
                response = export_to_csv(request, report_type)
            elif format_type == "pdf":
                response = export_to_pdf(request, report_type, include_charts)
            else:
                messages.error(request, "Format d'export invalide.")
                return redirect("reports:export_report")

            if email_to:
                send_report_email(email_to, response, report_type, format_type)
                messages.success(request, f"Rapport envoyé par email à {email_to}")
                return redirect("reports:dashboard")

            return response
    else:
        form = ReportExportForm()

    return render(request, "reports/export.html", {"form": form})


def export_to_excel(request, report_type):
    """Export report to Excel format"""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rapport"

    if report_type == "profit_analysis":
        ws.append(
            [
                "Date",
                "Véhicules",
                "Client",
                "Trader",
                "Prix de Vente (DA)",
                "Marge (DA)",
                "Commission (DA)",
            ]
        )
        sales = (
            Sale.objects.filter(is_finalized=True)
            .select_related("customer", "assigned_trader")
            .prefetch_related(
                "line_items__vehicle__purchase_line_item__purchase__freight_cost",
                "line_items__vehicle__purchase_line_item__purchase__customs_declaration",
            )
            .order_by("-sale_date")[:500]
        )
        for sale in sales:
            ws.append(
                [
                    sale.sale_date.strftime("%d/%m/%Y"),
                    sale.vehicles_display,
                    sale.customer.name,
                    sale.assigned_trader.get_full_name()
                    or sale.assigned_trader.username,
                    float(sale.sale_price),
                    float(sale.margin_amount),
                    float(sale.commission_amount or 0),
                ]
            )

    elif report_type == "inventory_status":
        ws.append(
            [
                "Marque",
                "Modèle",
                "Année",
                "Couleur",
                "VIN/Châssis",
                "Statut",
                "Jours en stock",
                "Coût de revient (DA)",
                "Fournisseur",
            ]
        )
        vehicles = Vehicle.objects.select_related(
            "purchase_line_item__purchase__supplier",
            "purchase_line_item__purchase__freight_cost",
            "purchase_line_item__purchase__customs_declaration",
        ).order_by("status", "-created_at")[:500]
        for v in vehicles:
            supplier = (
                v.purchase_line_item.purchase.supplier.name
                if v.purchase_line_item_id
                else "—"
            )
            ws.append(
                [
                    v.make,
                    v.model,
                    v.year,
                    v.color,
                    v.vin_chassis,
                    v.get_status_display(),
                    v.days_in_stock,
                    float(v.landed_cost),
                    supplier,
                ]
            )

    elif report_type == "sales_summary":
        ws.append(
            [
                "Date",
                "N° Vente",
                "Véhicules",
                "Client",
                "Trader",
                "Mode paiement",
                "Prix de Vente (DA)",
                "Commission (DA)",
            ]
        )
        sales = (
            Sale.objects.filter(is_finalized=True)
            .select_related("customer", "assigned_trader")
            .prefetch_related("line_items__vehicle")
            .order_by("-sale_date")[:500]
        )
        for sale in sales:
            ws.append(
                [
                    sale.sale_date.strftime("%d/%m/%Y"),
                    sale.sale_number,
                    sale.vehicles_display,
                    sale.customer.name,
                    sale.assigned_trader.get_full_name()
                    or sale.assigned_trader.username,
                    sale.get_payment_method_display(),
                    float(sale.sale_price),
                    float(sale.commission_amount or 0),
                ]
            )

    elif report_type == "payment_status":
        ws.append(
            [
                "N° Facture",
                "Client",
                "Date facture",
                "Échéance",
                "Total TTC (DA)",
                "Payé (DA)",
                "Solde dû (DA)",
                "Statut",
            ]
        )
        invoices = Invoice.objects.select_related("customer").order_by("-invoice_date")[
            :500
        ]
        for inv in invoices:
            ws.append(
                [
                    inv.invoice_number,
                    inv.customer.name,
                    inv.invoice_date.strftime("%d/%m/%Y"),
                    inv.due_date.strftime("%d/%m/%Y"),
                    float(inv.total_ttc),
                    float(inv.amount_paid),
                    float(inv.balance_due),
                    inv.get_status_display(),
                ]
            )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="rapport_{report_type}.xlsx"'
    )
    wb.save(response)
    return response


def export_to_csv(request, report_type):
    """Export report to CSV format"""
    import csv

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = (
        f'attachment; filename="rapport_{report_type}.csv"'
    )
    writer = csv.writer(response)

    if report_type == "profit_analysis":
        writer.writerow(
            [
                "Date",
                "Véhicules",
                "Client",
                "Trader",
                "Prix de Vente (DA)",
                "Marge (DA)",
                "Commission (DA)",
            ]
        )
        sales = (
            Sale.objects.filter(is_finalized=True)
            .select_related("customer", "assigned_trader")
            .prefetch_related(
                "line_items__vehicle__purchase_line_item__purchase__freight_cost",
                "line_items__vehicle__purchase_line_item__purchase__customs_declaration",
            )
            .order_by("-sale_date")[:500]
        )
        for sale in sales:
            writer.writerow(
                [
                    sale.sale_date.strftime("%d/%m/%Y"),
                    sale.vehicles_display,
                    sale.customer.name,
                    sale.assigned_trader.get_full_name()
                    or sale.assigned_trader.username,
                    float(sale.sale_price),
                    float(sale.margin_amount),
                    float(sale.commission_amount or 0),
                ]
            )

    elif report_type == "inventory_status":
        writer.writerow(
            [
                "Marque",
                "Modèle",
                "Année",
                "VIN/Châssis",
                "Statut",
                "Jours en stock",
                "Coût de revient (DA)",
                "Fournisseur",
            ]
        )
        vehicles = Vehicle.objects.select_related(
            "purchase_line_item__purchase__supplier",
            "purchase_line_item__purchase__freight_cost",
            "purchase_line_item__purchase__customs_declaration",
        ).order_by("status")[:500]
        for v in vehicles:
            supplier = (
                v.purchase_line_item.purchase.supplier.name
                if v.purchase_line_item_id
                else "—"
            )
            writer.writerow(
                [
                    v.make,
                    v.model,
                    v.year,
                    v.vin_chassis,
                    v.get_status_display(),
                    v.days_in_stock,
                    float(v.landed_cost),
                    supplier,
                ]
            )

    elif report_type == "sales_summary":
        writer.writerow(
            [
                "Date",
                "N° Vente",
                "Véhicules",
                "Client",
                "Mode paiement",
                "Prix de Vente (DA)",
                "Commission (DA)",
            ]
        )
        sales = (
            Sale.objects.filter(is_finalized=True)
            .select_related("customer", "assigned_trader")
            .prefetch_related("line_items__vehicle")
            .order_by("-sale_date")[:500]
        )
        for sale in sales:
            writer.writerow(
                [
                    sale.sale_date.strftime("%d/%m/%Y"),
                    sale.sale_number,
                    sale.vehicles_display,
                    sale.customer.name,
                    sale.get_payment_method_display(),
                    float(sale.sale_price),
                    float(sale.commission_amount or 0),
                ]
            )

    elif report_type == "payment_status":
        writer.writerow(
            [
                "N° Facture",
                "Client",
                "Échéance",
                "Total TTC (DA)",
                "Payé (DA)",
                "Solde dû (DA)",
                "Statut",
            ]
        )
        invoices = Invoice.objects.select_related("customer").order_by("-invoice_date")[
            :500
        ]
        for inv in invoices:
            writer.writerow(
                [
                    inv.invoice_number,
                    inv.customer.name,
                    inv.due_date.strftime("%d/%m/%Y"),
                    float(inv.total_ttc),
                    float(inv.amount_paid),
                    float(inv.balance_due),
                    inv.get_status_display(),
                ]
            )

    return response


def export_to_pdf(request, report_type, include_charts=False):
    """Export report to printable HTML/PDF"""
    from django.template.loader import render_to_string

    context = {"report_type": report_type, "request": request}
    html_content = render_to_string("reports/pdf_export.html", context, request=request)

    response = HttpResponse(html_content, content_type="text/html; charset=utf-8")
    response["Content-Disposition"] = f'inline; filename="rapport_{report_type}.html"'
    return response


def send_report_email(email_to, attachment, report_type, format_type):
    """Send report via email"""
    from django.core.mail import EmailMessage

    subject = f"Rapport {report_type} — {timezone.now().strftime('%d/%m/%Y')}"
    body = (
        f"Veuillez trouver ci-joint le rapport {report_type} au format {format_type}."
    )

    email = EmailMessage(subject=subject, body=body, to=[email_to])
    filename = f"rapport_{report_type}.{format_type}"
    email.attach(
        filename,
        attachment.content,
        attachment.get("Content-Type", "application/octet-stream"),
    )
    email.send()


@login_required
def ajax_chart_data(request):
    """AJAX endpoint for chart data"""

    chart_type = request.GET.get("type")
    try:
        period = int(request.GET.get("period", "6"))
    except ValueError:
        period = 6

    end_date = timezone.now().date()
    start_date = end_date.replace(day=1) - timedelta(days=period * 30)

    if chart_type == "monthly_sales":
        sales = Sale.objects.filter(
            sale_date__gte=start_date, sale_date__lte=end_date, is_finalized=True
        ).prefetch_related("line_items")

        from collections import defaultdict

        monthly_data = defaultdict(lambda: {"count": 0, "revenue": 0.0})

        for sale in sales:
            key = sale.sale_date.strftime("%Y-%m")
            monthly_data[key]["count"] += 1
            monthly_data[key]["revenue"] += float(sale.sale_price)

        sorted_keys = sorted(monthly_data.keys())
        chart_data = {
            "labels": [
                datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in sorted_keys
            ],
            "datasets": [
                {
                    "label": "Nombre de ventes",
                    "data": [monthly_data[m]["count"] for m in sorted_keys],
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                },
                {
                    "label": "Chiffre d'affaires (DA)",
                    "data": [monthly_data[m]["revenue"] for m in sorted_keys],
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                },
            ],
        }
        return JsonResponse(chart_data)

    elif chart_type == "inventory_status":
        status_data = Vehicle.objects.values("status").annotate(count=Count("id"))
        chart_data = {
            "labels": [
                item["status"].replace("_", " ").title() for item in status_data
            ],
            "datasets": [
                {
                    "data": [item["count"] for item in status_data],
                    "backgroundColor": [
                        "#FF6384",
                        "#36A2EB",
                        "#FFCE56",
                        "#4BC0C0",
                        "#9966FF",
                    ],
                }
            ],
        }
        return JsonResponse(chart_data)

    return JsonResponse({"error": "Invalid chart type"}, status=400)
