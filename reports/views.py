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
from sales.models import Sale, Invoice
from inventory.models import Vehicle
from payments.models import Payment
from commissions.models import CommissionSummary
from customers.models import Customer
from suppliers.models import Supplier
from core.decorators import manager_required


@login_required
def dashboard(request):
    """Reports dashboard with quick links and recent reports"""

    # Quick statistics
    today = timezone.now().date()
    current_month = today.replace(day=1)

    # Sales statistics
    monthly_sales = Sale.objects.filter(sale_date__gte=current_month, is_finalized=True)

    # Inventory statistics
    inventory_stats = {
        "total_vehicles": Vehicle.objects.count(),
        "available_vehicles": Vehicle.objects.filter(status="available").count(),
        "in_transit": Vehicle.objects.filter(status="in_transit").count(),
        "at_customs": Vehicle.objects.filter(status="at_customs").count(),
    }

    # Financial statistics
    financial_stats = {
        "monthly_revenue": monthly_sales.aggregate(Sum("sale_price"))["sale_price__sum"]
        or 0,
        "monthly_margin": sum(sale.margin_amount for sale in monthly_sales),
        "outstanding_invoices": Invoice.objects.filter(balance_due__gt=0).count(),
        "total_outstanding": Invoice.objects.filter(balance_due__gt=0).aggregate(
            Sum("balance_due")
        )["balance_due__sum"]
        or 0,
    }

    # Top performers (current month)
    top_traders = (
        monthly_sales.values(
            "assigned_trader__first_name", "assigned_trader__last_name"
        )
        .annotate(
            sales_count=Count("id"),
            total_revenue=Sum("sale_price"),
            total_commission=Sum("commission_amount"),
        )
        .order_by("-total_revenue")[:5]
    )

    # Recent activity
    recent_sales = (
        Sale.objects.filter(is_finalized=True)
        .select_related("vehicle", "customer", "assigned_trader")
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

    # Base queryset
    sales = Sale.objects.filter(is_finalized=True).select_related(
        "vehicle__vehicle_purchase__supplier", "customer", "assigned_trader"
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

        vehicle_make = form.cleaned_data.get("vehicle_make")
        if vehicle_make:
            sales = sales.filter(vehicle__make__icontains=vehicle_make)

        min_margin = form.cleaned_data.get("min_margin")
        if min_margin:
            # Filter by calculated margin
            sales = [sale for sale in sales if sale.margin_amount >= min_margin]

    # Role-based filtering
    if hasattr(request.user, "userprofile"):
        if request.user.userprofile.is_trader:
            sales = sales.filter(assigned_trader=request.user)

    # Calculate totals
    total_sales = len(sales) if isinstance(sales, list) else sales.count()
    total_revenue = sum(sale.sale_price for sale in sales)
    total_margin = sum(sale.margin_amount for sale in sales)
    total_commission = sum(sale.commission_amount or 0 for sale in sales)

    # Calculate averages
    avg_sale_price = total_revenue / total_sales if total_sales > 0 else 0
    avg_margin = total_margin / total_sales if total_sales > 0 else 0
    margin_percentage = (total_margin / total_revenue * 100) if total_revenue > 0 else 0

    # Group by analysis
    grouped_data = []
    if form.is_valid():
        group_by = form.cleaned_data.get("group_by", "month")

        if group_by == "month":
            # Group by month
            from collections import defaultdict

            monthly_data = defaultdict(
                lambda: {"sales_count": 0, "revenue": 0, "margin": 0, "commission": 0}
            )

            for sale in sales:
                month_key = sale.sale_date.strftime("%Y-%m")
                monthly_data[month_key]["sales_count"] += 1
                monthly_data[month_key]["revenue"] += sale.sale_price
                monthly_data[month_key]["margin"] += sale.margin_amount
                monthly_data[month_key]["commission"] += sale.commission_amount or 0

            grouped_data = [
                {
                    "label": datetime.strptime(month, "%Y-%m").strftime("%B %Y"),
                    "sales_count": data["sales_count"],
                    "revenue": data["revenue"],
                    "margin": data["margin"],
                    "commission": data["commission"],
                    "margin_percentage": (
                        (data["margin"] / data["revenue"] * 100)
                        if data["revenue"] > 0
                        else 0
                    ),
                }
                for month, data in sorted(monthly_data.items())
            ]

        elif group_by == "trader":
            # Group by trader
            from collections import defaultdict

            trader_data = defaultdict(
                lambda: {"sales_count": 0, "revenue": 0, "margin": 0, "commission": 0}
            )

            for sale in sales:
                trader_name = (
                    sale.assigned_trader.get_full_name()
                    or sale.assigned_trader.username
                )
                trader_data[trader_name]["sales_count"] += 1
                trader_data[trader_name]["revenue"] += sale.sale_price
                trader_data[trader_name]["margin"] += sale.margin_amount
                trader_data[trader_name]["commission"] += sale.commission_amount or 0

            grouped_data = [
                {
                    "label": trader,
                    "sales_count": data["sales_count"],
                    "revenue": data["revenue"],
                    "margin": data["margin"],
                    "commission": data["commission"],
                    "margin_percentage": (
                        (data["margin"] / data["revenue"] * 100)
                        if data["revenue"] > 0
                        else 0
                    ),
                }
                for trader, data in sorted(trader_data.items())
            ]

    # Top performing vehicles
    vehicle_performance = {}
    for sale in sales:
        vehicle_key = f"{sale.vehicle.make} {sale.vehicle.model}"
        if vehicle_key not in vehicle_performance:
            vehicle_performance[vehicle_key] = {"count": 0, "revenue": 0, "margin": 0}
        vehicle_performance[vehicle_key]["count"] += 1
        vehicle_performance[vehicle_key]["revenue"] += sale.sale_price
        vehicle_performance[vehicle_key]["margin"] += sale.margin_amount

    top_vehicles = sorted(
        [
            {
                "vehicle": vehicle,
                "count": data["count"],
                "revenue": data["revenue"],
                "margin": data["margin"],
                "avg_margin": data["margin"] / data["count"],
            }
            for vehicle, data in vehicle_performance.items()
        ],
        key=lambda x: x["margin"],
        reverse=True,
    )[:10]

    # Pre-serialize chart data as JSON to avoid locale number-formatting issues in JS
    # (French/Algerian locale renders 8600279 as "8 600 279,00" which breaks JS array syntax)
    import json as _json
    from decimal import Decimal

    def _f(v):
        return float(v) if isinstance(v, Decimal) else float(v or 0)

    chart_grouped_data = _json.dumps(
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
        # JSON-safe chart payload (bypasses locale formatting)
        "chart_grouped_data": chart_grouped_data,
    }

    return render(request, "reports/profit_analysis.html", context)


@login_required
def inventory_status(request):
    """Inventory status report"""

    form = InventoryStatusForm(request.GET or None)

    # Base queryset
    vehicles = Vehicle.objects.select_related(
        "vehicle_purchase__supplier", "reserved_by"
    )

    # Apply filters
    if form.is_valid():
        status = form.cleaned_data.get("status")
        if status:
            vehicles = vehicles.filter(status__in=status)

        supplier = form.cleaned_data.get("supplier")
        if supplier:
            vehicles = vehicles.filter(vehicle_purchase__supplier=supplier)

        vehicle_make = form.cleaned_data.get("vehicle_make")
        if vehicle_make:
            vehicles = vehicles.filter(make__icontains=vehicle_make)

        year_from = form.cleaned_data.get("year_from")
        if year_from:
            vehicles = vehicles.filter(year__gte=year_from)

        year_to = form.cleaned_data.get("year_to")
        if year_to:
            vehicles = vehicles.filter(year__lte=year_to)

        min_landed_cost = form.cleaned_data.get("min_landed_cost")
        if min_landed_cost:
            # Filter by calculated landed cost
            vehicles = [v for v in vehicles if v.landed_cost >= min_landed_cost]

        max_landed_cost = form.cleaned_data.get("max_landed_cost")
        if max_landed_cost:
            vehicles = [v for v in vehicles if v.landed_cost <= max_landed_cost]

        days_in_stock_min = form.cleaned_data.get("days_in_stock_min")
        if days_in_stock_min:
            vehicles = [v for v in vehicles if v.days_in_stock >= days_in_stock_min]

    # Calculate statistics
    if isinstance(vehicles, list):
        total_vehicles = len(vehicles)
        total_value = sum(v.landed_cost for v in vehicles)
    else:
        total_vehicles = vehicles.count()
        total_value = sum(v.landed_cost for v in vehicles)

    avg_value = total_value / total_vehicles if total_vehicles > 0 else 0

    # Status breakdown
    if not isinstance(vehicles, list):
        vehicles_list = list(vehicles)
    else:
        vehicles_list = vehicles

    status_breakdown = {}
    for vehicle in vehicles_list:
        status = vehicle.get_status_display()
        if status not in status_breakdown:
            status_breakdown[status] = {"count": 0, "value": 0}
        status_breakdown[status]["count"] += 1
        status_breakdown[status]["value"] += vehicle.landed_cost

    # Supplier breakdown
    supplier_breakdown = {}
    for vehicle in vehicles_list:
        supplier = vehicle.vehicle_purchase.supplier.name
        if supplier not in supplier_breakdown:
            supplier_breakdown[supplier] = {"count": 0, "value": 0}
        supplier_breakdown[supplier]["count"] += 1
        supplier_breakdown[supplier]["value"] += vehicle.landed_cost

    # Age analysis
    age_breakdown = {
        "0-30 days": {"count": 0, "value": 0},
        "31-60 days": {"count": 0, "value": 0},
        "61-90 days": {"count": 0, "value": 0},
        "90+ days": {"count": 0, "value": 0},
    }

    for vehicle in vehicles_list:
        days = vehicle.days_in_stock
        if days <= 30:
            category = "0-30 days"
        elif days <= 60:
            category = "31-60 days"
        elif days <= 90:
            category = "61-90 days"
        else:
            category = "90+ days"

        age_breakdown[category]["count"] += 1
        age_breakdown[category]["value"] += vehicle.landed_cost

    # Slow-moving vehicles (90+ days)
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
        "vehicles_list": vehicles_list[:50],  # Show first 50 for detail
    }

    return render(request, "reports/inventory_status.html", context)


@login_required
def sales_summary(request):
    """Sales summary report"""

    form = SalesSummaryForm(request.GET or None)

    # Base queryset
    sales = Sale.objects.filter(is_finalized=True).select_related(
        "vehicle", "customer", "assigned_trader"
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

    # Calculate totals
    total_sales = sales.count()
    total_revenue = sales.aggregate(Sum("sale_price"))["sale_price__sum"] or 0
    total_commission = (
        sales.aggregate(Sum("commission_amount"))["commission_amount__sum"] or 0
    )
    avg_sale_price = total_revenue / total_sales if total_sales > 0 else 0

    # Period analysis
    period_data = []
    if form.is_valid():
        period_type = form.cleaned_data.get("period_type", "monthly")

        if period_type == "monthly":
            # Group by month
            from collections import defaultdict

            monthly_data = defaultdict(
                lambda: {"sales_count": 0, "revenue": 0, "commission": 0}
            )

            for sale in sales:
                month_key = sale.sale_date.strftime("%Y-%m")
                monthly_data[month_key]["sales_count"] += 1
                monthly_data[month_key]["revenue"] += sale.sale_price
                monthly_data[month_key]["commission"] += sale.commission_amount or 0

            period_data = [
                {
                    "period": datetime.strptime(month, "%Y-%m").strftime("%B %Y"),
                    "sales_count": data["sales_count"],
                    "revenue": data["revenue"],
                    "commission": data["commission"],
                    "avg_sale": (
                        data["revenue"] / data["sales_count"]
                        if data["sales_count"] > 0
                        else 0
                    ),
                }
                for month, data in sorted(monthly_data.items())
            ]

    # Payment method breakdown – enriched with human-readable display labels
    PAYMENT_METHOD_LABELS = {
        "cash": "Cash",
        "bank_transfer": "Bank Transfer",
        "installment": "Installment",
        "check": "Check",
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
        .annotate(count=Count("id"), revenue=Sum("sale_price"))
        .order_by("-revenue")
    ]

    # Top customers
    top_customers = (
        sales.values("customer__name")
        .annotate(sales_count=Count("id"), total_spent=Sum("sale_price"))
        .order_by("-total_spent")[:10]
    )

    # Vehicle make performance
    make_performance = (
        sales.values("vehicle__make")
        .annotate(count=Count("id"), revenue=Sum("sale_price"))
        .order_by("-revenue")[:10]
    )

    # Pre-serialize chart data as JSON to avoid locale number-formatting issues in JS
    # (French/Algerian locale formats numbers as "8 600 279,00" which breaks JS array syntax)
    import json as _json
    from decimal import Decimal

    def _to_float(v):
        return float(v) if isinstance(v, Decimal) else float(v or 0)

    chart_period_data = _json.dumps(
        {
            "periods": [row["period"] for row in period_data],
            "revenues": [_to_float(row["revenue"]) for row in period_data],
            "saleCounts": [row["sales_count"] for row in period_data],
        }
    )

    chart_payment_data = _json.dumps(
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
        # JSON-safe chart payloads (bypasses locale formatting)
        "chart_period_data": chart_period_data,
        "chart_payment_data": chart_payment_data,
    }

    return render(request, "reports/sales_summary.html", context)


@login_required
def payment_status(request):
    """Payment status report"""

    form = PaymentStatusForm(request.GET or None)

    # Base queryset
    invoices = Invoice.objects.select_related(
        "customer", "sale__assigned_trader", "sale__vehicle"
    ).prefetch_related("payments")

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

    # Calculate statistics
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(Sum("total_ttc"))["total_ttc__sum"] or 0
    total_paid = invoices.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    total_outstanding = invoices.aggregate(Sum("balance_due"))["balance_due__sum"] or 0

    # Status breakdown
    status_breakdown = invoices.values("status").annotate(
        count=Count("id"), amount=Sum("total_ttc"), outstanding=Sum("balance_due")
    )

    # Overdue analysis
    overdue_invoices = invoices.filter(
        due_date__lt=timezone.now().date(), balance_due__gt=0
    )

    overdue_breakdown = {
        "1-30 days": {"count": 0, "amount": 0},
        "31-60 days": {"count": 0, "amount": 0},
        "61-90 days": {"count": 0, "amount": 0},
        "90+ days": {"count": 0, "amount": 0},
    }

    for invoice in overdue_invoices:
        days_overdue = invoice.days_overdue
        if days_overdue <= 30:
            category = "1-30 days"
        elif days_overdue <= 60:
            category = "31-60 days"
        elif days_overdue <= 90:
            category = "61-90 days"
        else:
            category = "90+ days"

        overdue_breakdown[category]["count"] += 1
        overdue_breakdown[category]["amount"] += invoice.balance_due

    # Top outstanding customers
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
        "invoices_list": invoices[:50],  # Show first 50 for detail
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

            # Get report data from session or regenerate
            report_type = request.session.get("last_report_type", "profit_analysis")

            if format_type == "excel":
                response = export_to_excel(request, report_type)
            elif format_type == "csv":
                response = export_to_csv(request, report_type)
            elif format_type == "pdf":
                response = export_to_pdf(request, report_type, include_charts)

            if email_to:
                # Send email with attachment
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
    from django.http import HttpResponse

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rapport"

    # Add headers and data based on report type
    if report_type == "profit_analysis":
        # Add profit analysis data
        ws.append(
            ["Date", "Véhicule", "Client", "Prix de Vente", "Marge", "Commission"]
        )

        # Get sales data (simplified)
        sales = Sale.objects.filter(is_finalized=True)[:100]
        for sale in sales:
            ws.append(
                [
                    sale.sale_date.strftime("%d/%m/%Y"),
                    f"{sale.vehicle.make} {sale.vehicle.model}",
                    sale.customer.name,
                    float(sale.sale_price),
                    float(sale.margin_amount),
                    float(sale.commission_amount or 0),
                ]
            )

    # Create response
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
    from django.http import HttpResponse

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="rapport_{report_type}.csv"'
    )

    writer = csv.writer(response)

    if report_type == "profit_analysis":
        writer.writerow(
            ["Date", "Véhicule", "Client", "Prix de Vente", "Marge", "Commission"]
        )

        sales = Sale.objects.filter(is_finalized=True)[:100]
        for sale in sales:
            writer.writerow(
                [
                    sale.sale_date.strftime("%d/%m/%Y"),
                    f"{sale.vehicle.make} {sale.vehicle.model}",
                    sale.customer.name,
                    float(sale.sale_price),
                    float(sale.margin_amount),
                    float(sale.commission_amount or 0),
                ]
            )

    return response


def export_to_pdf(request, report_type, include_charts=False):
    """Export report to PDF format"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string

    # For now, return HTML that can be printed to PDF
    # In production, you might want to use a library like WeasyPrint

    context = {"report_type": report_type}
    html_content = render_to_string("reports/pdf_export.html", context)

    response = HttpResponse(html_content, content_type="text/html")
    response["Content-Disposition"] = (
        f'attachment; filename="rapport_{report_type}.html"'
    )

    return response


def send_report_email(email_to, attachment, report_type, format_type):
    """Send report via email"""
    from django.core.mail import EmailMessage

    subject = f"Rapport {report_type} - {timezone.now().strftime('%d/%m/%Y')}"
    body = (
        f"Veuillez trouver ci-joint le rapport {report_type} au format {format_type}."
    )

    email = EmailMessage(subject=subject, body=body, to=[email_to])

    # Attach file
    filename = f"rapport_{report_type}.{format_type}"
    email.attach(filename, attachment.content, attachment["Content-Type"])

    email.send()


@login_required
def ajax_chart_data(request):
    """AJAX endpoint for chart data"""

    chart_type = request.GET.get("type")
    period = request.GET.get("period", "6")  # months

    try:
        period = int(period)
    except ValueError:
        period = 6

    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date.replace(day=1) - timedelta(days=period * 30)

    if chart_type == "monthly_sales":
        # Monthly sales chart
        sales = Sale.objects.filter(
            sale_date__gte=start_date, sale_date__lte=end_date, is_finalized=True
        )

        from collections import defaultdict

        monthly_data = defaultdict(lambda: {"count": 0, "revenue": 0})

        for sale in sales:
            month_key = sale.sale_date.strftime("%Y-%m")
            monthly_data[month_key]["count"] += 1
            monthly_data[month_key]["revenue"] += float(sale.sale_price)

        chart_data = {
            "labels": [
                datetime.strptime(month, "%Y-%m").strftime("%b %Y")
                for month in sorted(monthly_data.keys())
            ],
            "datasets": [
                {
                    "label": "Nombre de ventes",
                    "data": [data["count"] for data in monthly_data.values()],
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                },
                {
                    "label": "Chiffre d'affaires (DA)",
                    "data": [data["revenue"] for data in monthly_data.values()],
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                },
            ],
        }

        return JsonResponse(chart_data)

    elif chart_type == "inventory_status":
        # Inventory status pie chart
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

    return JsonResponse({"error": "Invalid chart type"})
