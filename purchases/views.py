from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import Purchase, FreightCost, CustomsDeclaration
from .forms import (
    PurchaseForm, FreightCostForm, CustomsDeclarationForm, 
    PurchaseSearchForm
)
from inventory.models import Vehicle
from core.decorators import finance_required
from core.utils import TaxCalculator

@login_required
def purchase_list(request):
    """List all purchases with search and filter capabilities"""
    
    purchases = Purchase.objects.select_related(
        'supplier', 'currency', 'customs_declaration'
    ).prefetch_related(
        Prefetch('vehicle_set', queryset=Vehicle.objects.select_related('vehicle_purchase'))
    )
    
    search_form = PurchaseSearchForm(request.GET)
    
    # Apply filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        if search:
            purchases = purchases.filter(
                Q(supplier__name__icontains=search) |
                Q(customs_declaration__declaration_number__icontains=search) |
                Q(notes__icontains=search)
            )
        
        supplier = search_form.cleaned_data.get('supplier')
        if supplier:
            purchases = purchases.filter(supplier=supplier)
        
        date_from = search_form.cleaned_data.get('date_from')
        if date_from:
            purchases = purchases.filter(purchase_date__gte=date_from)
        
        date_to = search_form.cleaned_data.get('date_to')
        if date_to:
            purchases = purchases.filter(purchase_date__lte=date_to)
        
        currency = search_form.cleaned_data.get('currency')
        if currency:
            purchases = purchases.filter(currency=currency)
        
        customs_status = search_form.cleaned_data.get('customs_status')
        if customs_status == 'pending':
            purchases = purchases.filter(
                Q(customs_declaration__isnull=True) |
                Q(customs_declaration__is_cleared=False)
            )
        elif customs_status == 'cleared':
            purchases = purchases.filter(customs_declaration__is_cleared=True)
    
    # Pagination
    paginator = Paginator(purchases, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': purchases.count(),
    }
    
    return render(request, 'purchases/list.html', context)

@finance_required
def purchase_create(request):
    """Create new vehicle purchase"""
    
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.created_by = request.user
            purchase.save()
            messages.success(request, "Achat enregistré avec succès.")
            return redirect('purchases:detail', pk=purchase.pk)
    else:
        form = PurchaseForm()
    
    return render(request, 'purchases/form.html', {
        'form': form,
        'title': 'Nouvel Achat de Véhicule'
    })

@login_required
def purchase_detail(request, pk):
    """Purchase detail view with all costs"""
    
    purchase = get_object_or_404(
        Purchase.objects.select_related(
            'supplier', 'currency', 'freight_cost', 'customs_declaration'
        ).prefetch_related('vehicle_set'),
        pk=pk
    )
    
    # Calculate totals
    freight_cost = getattr(purchase, 'freight_cost', None)
    customs = getattr(purchase, 'customs_declaration', None)
    
    # Landed cost calculation
    landed_cost_components = {
        'purchase_price': purchase.purchase_price_da or 0,
        'freight_cost': freight_cost.total_freight_cost_da if freight_cost else 0,
        'customs_cost': customs.total_customs_cost_da if customs else 0,
    }
    
    total_landed_cost = sum(landed_cost_components.values())
    
    # Status determination
    if customs and customs.is_cleared:
        status = 'cleared'
        status_display = 'Dédouané - En Stock'
        status_class = 'success'
    elif customs:
        status = 'at_customs'
        status_display = 'En Douane'
        status_class = 'warning'
    elif freight_cost:
        status = 'at_customs'
        status_display = 'Transport Enregistré - Attente Douane'
        status_class = 'info'
    else:
        status = 'in_transit'
        status_display = 'En Transit'
        status_class = 'secondary'
    
    context = {
        'purchase': purchase,
        'freight_cost': freight_cost,
        'customs': customs,
        'landed_cost_components': landed_cost_components,
        'total_landed_cost': total_landed_cost,
        'status': status,
        'status_display': status_display,
        'status_class': status_class,
        'vehicles': purchase.vehicle_set.all(),
    }
    
    return render(request, 'purchases/detail.html', context)

@finance_required
def purchase_add_freight(request, pk):
    """Add freight costs to purchase"""
    
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Check if freight costs already exist
    if hasattr(purchase, 'freight_cost'):
        messages.warning(request, "Les frais de transport sont déjà enregistrés.")
        return redirect('purchases:detail', pk=pk)
    
    if request.method == 'POST':
        form = FreightCostForm(request.POST)
        if form.is_valid():
            freight_cost = form.save(commit=False)
            freight_cost.purchase = purchase
            freight_cost.created_by = request.user
            freight_cost.save()
            
            messages.success(request, "Frais de transport enregistrés avec succès.")
            return redirect('purchases:detail', pk=pk)
    else:
        form = FreightCostForm()
    
    return render(request, 'purchases/freight_form.html', {
        'form': form,
        'purchase': purchase,
        'title': f'Frais de Transport - {purchase}'
    })

@finance_required
def purchase_add_customs(request, pk):
    """Add customs declaration and duties"""
    
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Check if customs already declared
    if hasattr(purchase, 'customs_declaration'):
        messages.warning(request, "La déclaration douanière existe déjà.")
        return redirect('purchases:detail', pk=pk)
    
    # Check if freight costs exist
    if not hasattr(purchase, 'freight_cost'):
        messages.error(request, "Veuillez d'abord enregistrer les frais de transport.")
        return redirect('purchases:add_freight', pk=pk)
    
    if request.method == 'POST':
        form = CustomsDeclarationForm(request.POST, purchase=purchase)
        if form.is_valid():
            customs = form.save(commit=False)
            customs.purchase = purchase
            customs.created_by = request.user
            
            # Auto-calculate CIF value
            customs.cif_value_da = customs.calculate_cif_value()
            
            customs.save()
            
            messages.success(request, "Déclaration douanière enregistrée avec succès.")
            return redirect('purchases:detail', pk=pk)
    else:
        form = CustomsDeclarationForm(purchase=purchase)
    
    return render(request, 'purchases/customs_form.html', {
        'form': form,
        'purchase': purchase,
        'title': f'Déclaration Douanière - {purchase}'
    })

@finance_required
def purchase_edit_freight(request, pk):
    """Edit freight costs"""
    
    purchase = get_object_or_404(Purchase, pk=pk)
    freight_cost = get_object_or_404(FreightCost, purchase=purchase)
    
    if request.method == 'POST':
        form = FreightCostForm(request.POST, instance=freight_cost)
        if form.is_valid():
            freight_cost = form.save(commit=False)
            freight_cost.updated_by = request.user
            freight_cost.save()
            
            messages.success(request, "Frais de transport modifiés avec succès.")
            return redirect('purchases:detail', pk=pk)
    else:
        form = FreightCostForm(instance=freight_cost)
    
    return render(request, 'purchases/freight_form.html', {
        'form': form,
        'purchase': purchase,
        'freight_cost': freight_cost,
        'title': f'Modifier Frais de Transport - {purchase}'
    })

@finance_required
def purchase_edit_customs(request, pk):
    """Edit customs declaration"""
    
    purchase = get_object_or_404(Purchase, pk=pk)
    customs = get_object_or_404(CustomsDeclaration, purchase=purchase)
    
    if request.method == 'POST':
        form = CustomsDeclarationForm(request.POST, instance=customs, purchase=purchase)
        if form.is_valid():
            customs = form.save(commit=False)
            customs.updated_by = request.user
            customs.save()
            
            messages.success(request, "Déclaration douanière modifiée avec succès.")
            return redirect('purchases:detail', pk=pk)
    else:
        form = CustomsDeclarationForm(instance=customs, purchase=purchase)
    
    return render(request, 'purchases/customs_form.html', {
        'form': form,
        'purchase': purchase,
        'customs': customs,
        'title': f'Modifier Déclaration Douanière - {purchase}'
    })

@login_required
def ajax_calculate_customs(request):
    """AJAX endpoint to calculate customs duties"""
    
    if request.method == 'POST':
        cif_value = float(request.POST.get('cif_value', 0))
        tariff_rate = float(request.POST.get('tariff_rate', 0))
        tva_rate = float(request.POST.get('tva_rate', 0))
        other_fees = float(request.POST.get('other_fees', 0))
        
        # Calculate import duty
        import_duty = cif_value * (tariff_rate / 100)
        
        # Calculate TVA
        taxable_base = cif_value + import_duty
        tva_amount = taxable_base * (tva_rate / 100)
        
        # Total customs cost
        total_customs_cost = import_duty + tva_amount + other_fees
        
        return JsonResponse({
            'import_duty': round(import_duty, 2),
            'tva_amount': round(tva_amount, 2),
            'total_customs_cost': round(total_customs_cost, 2)
        })
    
    return JsonResponse({'error': 'Invalid request'})

@finance_required
def customs_mark_cleared(request, pk):
    """Mark customs as cleared via AJAX"""
    
    if request.method == 'POST':
        customs = get_object_or_404(CustomsDeclaration, pk=pk)
        
        customs.is_cleared = True
        customs.clearance_date = timezone.now().date()
        customs.updated_by = request.user
        customs.save()
        
        # Update vehicle status to available
        for vehicle in customs.purchase.vehicle_set.all():
            vehicle.status = 'available'
            vehicle.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Véhicule dédouané et ajouté au stock.',
            'clearance_date': customs.clearance_date.strftime('%d/%m/%Y')
        })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})