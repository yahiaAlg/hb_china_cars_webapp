from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import (
    CommissionTier,
    CommissionPeriod,
    CommissionSummary,
)
from .forms import (
    CommissionTierForm,
    CommissionAdjustmentForm,
    CommissionPaymentForm,
    CommissionReportForm,
    TraderPerformanceFilterForm,
)
from sales.models import Sale
from core.decorators import manager_required


def commission_index(request):
    """Route to the appropriate commissions page based on role."""
    if hasattr(request.user, "userprofile") and request.user.userprofile.is_trader:
        return redirect("commissions:my_commission")
    return redirect("commissions:overview")


@login_required
def my_commission(request):
    """Trader's own commission view"""

    # Check if user is a trader
    if (
        not hasattr(request.user, "userprofile")
        or not request.user.userprofile.is_trader
    ):
        messages.error(request, "Accès réservé aux traders.")
        return redirect("core:dashboard")

    # Get current month and year
    today = timezone.now().date()
    current_year = request.GET.get("year", today.year)
    current_month = request.GET.get("month", today.month)

    try:
        current_year = int(current_year)
        current_month = int(current_month)
    except (ValueError, TypeError):
        current_year = today.year
        current_month = today.month

    # Get sales for current period
    sales = Sale.objects.filter(
        assigned_trader=request.user,
        sale_date__year=current_year,
        sale_date__month=current_month,
        is_finalized=True,
    ).select_related("vehicle", "customer", "invoice")

    # Calculate current period statistics
    current_stats = {
        "sales_count": sales.count(),
        "total_sales_value": sales.aggregate(Sum("sale_price"))["sale_price__sum"] or 0,
        "total_margin": sum(sale.margin_amount for sale in sales),
        "total_commission": sales.aggregate(Sum("commission_amount"))[
            "commission_amount__sum"
        ]
        or 0,
        "avg_commission_rate": 0,
    }

    if current_stats["total_margin"] > 0:
        current_stats["avg_commission_rate"] = (
            current_stats["total_commission"] / current_stats["total_margin"] * 100
        )

    # Get commission summary if period is closed
    try:
        period = CommissionPeriod.objects.get(year=current_year, month=current_month)
        commission_summary = CommissionSummary.objects.filter(
            trader=request.user, period=period
        ).first()
    except CommissionPeriod.DoesNotExist:
        period = None
        commission_summary = None

    # Get last 6 months performance
    performance_data = []
    for i in range(6):
        date = today.replace(day=1) - timedelta(days=i * 30)
        month_sales = Sale.objects.filter(
            assigned_trader=request.user,
            sale_date__year=date.year,
            sale_date__month=date.month,
            is_finalized=True,
        )

        performance_data.append(
            {
                "month": date.strftime("%b %Y"),
                "sales_count": month_sales.count(),
                "commission": month_sales.aggregate(Sum("commission_amount"))[
                    "commission_amount__sum"
                ]
                or 0,
            }
        )

    performance_data.reverse()

    # Get applicable commission tier
    applicable_tier = None
    if current_stats["sales_count"] > 0:
        applicable_tier = (
            CommissionTier.objects.filter(
                is_active=True, min_sales_count__lte=current_stats["sales_count"]
            )
            .filter(
                Q(max_sales_count__gte=current_stats["sales_count"])
                | Q(max_sales_count__isnull=True)
            )
            .first()
        )

    context = {
        "current_year": current_year,
        "current_month": current_month,
        "current_stats": current_stats,
        "sales": sales,
        "commission_summary": commission_summary,
        "period": period,
        "performance_data": performance_data,
        "applicable_tier": applicable_tier,
    }

    return render(request, "commissions/my_commission.html", context)


@manager_required
def commission_overview(request):
    """Manager overview of all commissions"""

    filter_form = CommissionReportForm(request.GET)

    # Get commission summaries
    summaries = CommissionSummary.objects.select_related(
        "trader__userprofile", "period"
    ).prefetch_related("commission_payment")

    # Apply filters
    if filter_form.is_valid():
        year = filter_form.cleaned_data.get("year")
        if year:
            summaries = summaries.filter(period__year=year)

        month = filter_form.cleaned_data.get("month")
        if month:
            summaries = summaries.filter(period__month=month)

        trader = filter_form.cleaned_data.get("trader")
        if trader:
            summaries = summaries.filter(trader=trader)

        payout_status = filter_form.cleaned_data.get("payout_status")
        if payout_status:
            summaries = summaries.filter(payout_status=payout_status)

    # Calculate totals
    totals = summaries.aggregate(
        total_sales=Sum("sales_count"),
        total_sales_value=Sum("total_sales_value"),
        total_margin=Sum("total_margin"),
        total_commission=Sum("total_commission"),
        total_paid=Sum("commission_payment__amount_paid"),
    )

    # Outstanding commissions
    outstanding_summaries = summaries.filter(payout_status__in=["pending", "approved"])
    outstanding_total = (
        outstanding_summaries.aggregate(Sum("total_commission"))[
            "total_commission__sum"
        ]
        or 0
    )

    # Top performers (current month)
    today = timezone.now().date()
    current_month_summaries = summaries.filter(
        period__year=today.year, period__month=today.month
    ).order_by("-total_commission")[:5]

    # Pagination
    paginator = Paginator(summaries, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "filter_form": filter_form,
        "totals": totals,
        "outstanding_total": outstanding_total,
        "current_month_summaries": current_month_summaries,
        "total_count": summaries.count(),
    }

    return render(request, "commissions/overview.html", context)


@manager_required
def trader_performance(request):
    """Trader performance comparison"""

    filter_form = TraderPerformanceFilterForm(request.GET)

    # Get all traders
    traders = User.objects.filter(
        userprofile__role__in=["trader", "manager"], is_active=True
    ).select_related("userprofile")

    # Calculate performance metrics
    performance_data = []

    for trader in traders:
        # Get sales for the period
        sales = Sale.objects.filter(assigned_trader=trader, is_finalized=True)

        # Apply date filters
        if filter_form.is_valid():
            period_from = filter_form.cleaned_data.get("period_from")
            if period_from:
                sales = sales.filter(sale_date__gte=period_from)

            period_to = filter_form.cleaned_data.get("period_to")
            if period_to:
                sales = sales.filter(sale_date__lte=period_to)

            min_sales = filter_form.cleaned_data.get("min_sales")
            if min_sales and sales.count() < min_sales:
                continue

        # Calculate metrics
        sales_count = sales.count()
        if sales_count == 0:
            continue

        total_sales_value = sales.aggregate(Sum("sale_price"))["sale_price__sum"] or 0
        total_commission = (
            sales.aggregate(Sum("commission_amount"))["commission_amount__sum"] or 0
        )
        total_margin = sum(sale.margin_amount for sale in sales)

        avg_commission_rate = (
            (total_commission / total_margin * 100) if total_margin > 0 else 0
        )
        avg_sale_value = total_sales_value / sales_count if sales_count > 0 else 0

        performance_data.append(
            {
                "trader": trader,
                "sales_count": sales_count,
                "total_sales_value": total_sales_value,
                "total_margin": total_margin,
                "total_commission": total_commission,
                "avg_commission_rate": avg_commission_rate,
                "avg_sale_value": avg_sale_value,
            }
        )

    # Sort by selected criteria
    sort_by = "total_commission"
    if filter_form.is_valid():
        sort_by = filter_form.cleaned_data.get("sort_by", "total_commission")

    performance_data.sort(key=lambda x: x[sort_by], reverse=True)

    # Add ranking
    for i, data in enumerate(performance_data, 1):
        data["rank"] = i

    context = {
        "performance_data": performance_data,
        "filter_form": filter_form,
    }

    return render(request, "commissions/trader_performance.html", context)


@manager_required
def commission_tiers(request):
    """Manage commission tiers"""

    tiers = CommissionTier.objects.all()

    context = {
        "tiers": tiers,
    }

    return render(request, "commissions/tiers.html", context)


@manager_required
def commission_tier_create(request):
    """Create new commission tier"""

    if request.method == "POST":
        form = CommissionTierForm(request.POST)
        if form.is_valid():
            tier = form.save(commit=False)
            tier.created_by = request.user
            tier.save()

            messages.success(
                request, f"Niveau de commission '{tier.name}' créé avec succès."
            )
            return redirect("commissions:tiers")
    else:
        form = CommissionTierForm()

    return render(
        request,
        "commissions/tier_form.html",
        {"form": form, "title": "Nouveau Niveau de Commission"},
    )


@manager_required
def commission_tier_edit(request, pk):
    """Edit commission tier"""

    tier = get_object_or_404(CommissionTier, pk=pk)

    if request.method == "POST":
        form = CommissionTierForm(request.POST, instance=tier)
        if form.is_valid():
            tier = form.save(commit=False)
            tier.updated_by = request.user
            tier.save()

            messages.success(
                request, f"Niveau de commission '{tier.name}' modifié avec succès."
            )
            return redirect("commissions:tiers")
    else:
        form = CommissionTierForm(instance=tier)

    return render(
        request,
        "commissions/tier_form.html",
        {"form": form, "tier": tier, "title": f"Modifier {tier.name}"},
    )


@manager_required
def commission_adjustment_create(request, summary_id):
    """Create commission adjustment"""

    summary = get_object_or_404(CommissionSummary, pk=summary_id)

    if request.method == "POST":
        form = CommissionAdjustmentForm(request.POST, period=summary.period)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.approved_by = request.user
            adjustment.created_by = request.user
            adjustment.save()

            messages.success(
                request, "Ajustement de commission enregistré avec succès."
            )
            return redirect("commissions:overview")
    else:
        form = CommissionAdjustmentForm(period=summary.period)
        form.fields["trader"].initial = summary.trader

    return render(
        request,
        "commissions/adjustment_form.html",
        {
            "form": form,
            "summary": summary,
            "title": f"Ajustement - {summary.trader.get_full_name()}",
        },
    )


@manager_required
def commission_payment_create(request, summary_id):
    """Create commission payment"""

    summary = get_object_or_404(CommissionSummary, pk=summary_id)

    # Check if already paid
    if hasattr(summary, "commission_payment"):
        messages.warning(request, "Cette commission a déjà été payée.")
        return redirect("commissions:overview")

    if request.method == "POST":
        form = CommissionPaymentForm(request.POST, summary=summary)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.paid_by = request.user
            payment.created_by = request.user
            payment.save()

            messages.success(
                request,
                f"Paiement de commission enregistré pour {summary.trader.get_full_name()}.",
            )
            return redirect("commissions:overview")
    else:
        form = CommissionPaymentForm(summary=summary)

    return render(
        request,
        "commissions/payment_form.html",
        {
            "form": form,
            "summary": summary,
            "title": f"Paiement Commission - {summary.trader.get_full_name()}",
        },
    )


@manager_required
def close_commission_period(request, year, month):
    """Close commission period and calculate final commissions"""

    if request.method == "POST":
        # Get or create period
        period, created = CommissionPeriod.objects.get_or_create(
            year=year, month=month, defaults={"created_by": request.user}
        )

        if period.is_closed:
            return JsonResponse(
                {"success": False, "message": "Cette période est déjà fermée."}
            )

        # Close the period
        period.close_period(request.user)

        return JsonResponse(
            {
                "success": True,
                "message": f"Période {period} fermée et commissions calculées.",
            }
        )

    return JsonResponse({"success": False, "message": "Méthode non autorisée."})


@manager_required
def approve_commission(request, summary_id):
    """Approve commission for payment"""

    if request.method == "POST":
        summary = get_object_or_404(CommissionSummary, pk=summary_id)

        if summary.payout_status != "pending":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Cette commission ne peut pas être approuvée.",
                }
            )

        summary.payout_status = "approved"
        summary.updated_by = request.user
        summary.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Commission approuvée pour {summary.trader.get_full_name()}.",
            }
        )

    return JsonResponse({"success": False, "message": "Méthode non autorisée."})


@login_required
def ajax_commission_calculation(request):
    """AJAX endpoint for commission calculation preview"""

    trader_id = request.GET.get("trader_id")
    year = request.GET.get("year")
    month = request.GET.get("month")

    if not all([trader_id, year, month]):
        return JsonResponse({"error": "Missing parameters"})

    try:
        trader = User.objects.get(pk=trader_id)
        year = int(year)
        month = int(month)

        # Get sales for the period
        sales = Sale.objects.filter(
            assigned_trader=trader,
            sale_date__year=year,
            sale_date__month=month,
            is_finalized=True,
        )

        # Calculate metrics
        sales_count = sales.count()
        total_sales_value = sales.aggregate(Sum("sale_price"))["sale_price__sum"] or 0
        total_commission = (
            sales.aggregate(Sum("commission_amount"))["commission_amount__sum"] or 0
        )
        total_margin = sum(sale.margin_amount for sale in sales)

        # Find applicable tier
        applicable_tier = None
        tier_bonus = 0

        if sales_count > 0:
            applicable_tier = (
                CommissionTier.objects.filter(
                    is_active=True, min_sales_count__lte=sales_count
                )
                .filter(
                    Q(max_sales_count__gte=sales_count)
                    | Q(max_sales_count__isnull=True)
                )
                .first()
            )

            if applicable_tier:
                base_rate = 10.0  # Default base rate
                if applicable_tier.commission_rate > base_rate:
                    bonus_rate = applicable_tier.commission_rate - base_rate
                    tier_bonus = total_margin * (bonus_rate / 100)

        return JsonResponse(
            {
                "success": True,
                "sales_count": sales_count,
                "total_sales_value": float(total_sales_value),
                "total_margin": float(total_margin),
                "base_commission": float(total_commission),
                "tier_bonus": float(tier_bonus),
                "total_commission": float(total_commission + tier_bonus),
                "applicable_tier": applicable_tier.name if applicable_tier else None,
            }
        )

    except (User.DoesNotExist, ValueError):
        return JsonResponse({"error": "Invalid data"})
