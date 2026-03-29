from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Supplier
from .forms import SupplierForm, SupplierSearchForm
from core.decorators import finance_required


@login_required
def supplier_list(request):
    """List all suppliers with search and filter capabilities"""

    suppliers = Supplier.objects.all().select_related("currency")
    search_form = SupplierSearchForm(request.GET)

    # Apply filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get("search")
        if search:
            suppliers = suppliers.filter(
                Q(name__icontains=search)
                | Q(contact_person__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        country = search_form.cleaned_data.get("country")
        if country:
            suppliers = suppliers.filter(country__icontains=country)

        currency = search_form.cleaned_data.get("currency")
        if currency:
            suppliers = suppliers.filter(currency=currency)

        is_active = search_form.cleaned_data.get("is_active")
        if is_active == "true":
            suppliers = suppliers.filter(is_active=True)
        elif is_active == "false":
            suppliers = suppliers.filter(is_active=False)

    # Add annotations for purchase statistics
    suppliers = suppliers.annotate(
        purchase_count=Count("purchase"),
        total_purchase_value=Sum("purchase__purchase_price_da"),
    )

    # Pagination
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "total_count": suppliers.count(),
    }

    return render(request, "suppliers/list.html", context)


@finance_required
def supplier_create(request):
    """Create new supplier"""

    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            messages.success(
                request, f"Fournisseur '{supplier.name}' créé avec succès."
            )
            return redirect("suppliers:detail", pk=supplier.pk)
    else:
        form = SupplierForm()

    return render(
        request, "suppliers/form.html", {"form": form, "title": "Nouveau Fournisseur"}
    )


@login_required
def supplier_detail(request, pk):
    """Supplier detail view with purchase history"""

    supplier = get_object_or_404(Supplier, pk=pk)

    # Get purchase history
    purchases = supplier.purchase_set.all().select_related("currency")

    # Calculate statistics
    total_purchases = purchases.count()
    total_value = sum(p.purchase_price_da for p in purchases if p.purchase_price_da)
    avg_value = total_value / total_purchases if total_purchases > 0 else 0

    # Recent purchases
    recent_purchases = purchases.order_by("-purchase_date")[:5]

    context = {
        "supplier": supplier,
        "total_purchases": total_purchases,
        "total_value": total_value,
        "avg_value": avg_value,
        "recent_purchases": recent_purchases,
    }

    return render(request, "suppliers/detail.html", context)


@finance_required
def supplier_edit(request, pk):
    """Edit supplier"""

    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.updated_by = request.user
            supplier.save()
            messages.success(
                request, f"Fournisseur '{supplier.name}' modifié avec succès."
            )
            return redirect("suppliers:detail", pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)

    return render(
        request,
        "suppliers/form.html",
        {"form": form, "supplier": supplier, "title": f"Modifier {supplier.name}"},
    )


@finance_required
def supplier_toggle_status(request, pk):
    """Toggle supplier active status via AJAX"""

    if request.method == "POST":
        supplier = get_object_or_404(Supplier, pk=pk)

        # Check if supplier can be deactivated
        if supplier.is_active and supplier.has_purchases:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Impossible de désactiver un fournisseur avec des achats existants.",
                }
            )

        supplier.is_active = not supplier.is_active
        supplier.updated_by = request.user
        supplier.save()

        status_text = "activé" if supplier.is_active else "désactivé"

        return JsonResponse(
            {
                "success": True,
                "message": f"Fournisseur {status_text} avec succès.",
                "is_active": supplier.is_active,
            }
        )

    return JsonResponse({"success": False, "message": "Méthode non autorisée."})


@login_required
def supplier_ajax_search(request):
    """AJAX endpoint for supplier search in dropdowns"""

    term = request.GET.get("term", "")
    suppliers = Supplier.objects.filter(is_active=True, name__icontains=term)[:10]

    results = [
        {"id": supplier.id, "text": supplier.name, "currency": supplier.currency.code}
        for supplier in suppliers
    ]

    return JsonResponse({"results": results})
