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

    # Apply filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get("search")
        if search:
            customers = customers.filter(
                Q(name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
                | Q(nif_tax_id__icontains=search)
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
            # Filter customers with outstanding invoices
            customers = customers.filter(invoice__balance_due__gt=0).distinct()

    # Add annotations for statistics (use different names to avoid property conflicts)
    customers = customers.annotate(
        sales_count=Count("sale"),
        purchases_total=Sum("sale__sale_price"),
        last_sale_date=Max("sale__sale_date"),
    )

    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "total_count": customers.count(),
    }

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

    return render(
        request, "customers/form.html", {"form": form, "title": "Nouveau Client"}
    )


@login_required
def customer_detail(request, pk):
    """Customer detail view with purchase history"""

    customer = get_object_or_404(Customer, pk=pk)

    # Get purchase history
    sales = customer.sale_set.all().select_related("vehicle", "assigned_trader")

    # Get invoices and payments
    invoices = customer.invoice_set.all().order_by("-invoice_date")
    outstanding_invoices = invoices.filter(balance_due__gt=0)

    # Calculate statistics
    total_purchases = sales.count()
    total_value = sum(sale.sale_price for sale in sales)
    total_outstanding = sum(invoice.balance_due for invoice in outstanding_invoices)

    # Recent activity
    recent_sales = sales.order_by("-sale_date")[:5]
    recent_notes = customer.customer_notes.order_by("-created_at")[:5]

    # Forms
    note_form = CustomerNoteForm()

    context = {
        "customer": customer,
        "total_purchases": total_purchases,
        "total_value": total_value,
        "total_outstanding": total_outstanding,
        "recent_sales": recent_sales,
        "recent_notes": recent_notes,
        "outstanding_invoices": outstanding_invoices,
        "note_form": note_form,
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

    return render(
        request,
        "customers/form.html",
        {"form": form, "customer": customer, "title": f"Modifier {customer.name}"},
    )


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

    # If form invalid, redirect back to detail with form errors
    return redirect("customers:detail", pk=pk)


@login_required
def customer_ajax_search(request):
    """AJAX endpoint for customer search in dropdowns"""

    term = request.GET.get("term", "")
    customers = Customer.objects.filter(is_active=True).filter(
        Q(name__icontains=term) | Q(phone__icontains=term)
    )[:10]

    results = [
        {
            "id": customer.id,
            "text": f"{customer.name} - {customer.phone}",
            "name": customer.name,
            "phone": customer.phone,
            "address": customer.address,
            "customer_type": customer.customer_type,
            "nif_tax_id": customer.nif_tax_id,
            "wilaya": customer.wilaya,
        }
        for customer in customers
    ]

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

            return JsonResponse(
                {
                    "success": True,
                    "customer": {
                        "id": customer.id,
                        "name": customer.name,
                        "phone": customer.phone,
                        "address": customer.address,
                        "customer_type": customer.customer_type,
                        "nif_tax_id": customer.nif_tax_id,
                        "wilaya": customer.wilaya,
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    # Return form HTML for modal
    form = QuickCustomerForm()
    return render(request, "customers/quick_form.html", {"form": form})


@trader_required
def customer_toggle_status(request, pk):
    """Toggle customer active status via AJAX"""

    if request.method == "POST":
        customer = get_object_or_404(Customer, pk=pk)

        # Check if customer has outstanding balance
        if customer.is_active and customer.outstanding_balance > 0:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Impossible de désactiver un client avec un solde impayé.",
                }
            )

        customer.is_active = not customer.is_active
        customer.updated_by = request.user
        customer.save()

        status_text = "activé" if customer.is_active else "désactivé"

        return JsonResponse(
            {
                "success": True,
                "message": f"Client {status_text} avec succès.",
                "is_active": customer.is_active,
            }
        )

    return JsonResponse({"success": False, "message": "Méthode non autorisée."})
