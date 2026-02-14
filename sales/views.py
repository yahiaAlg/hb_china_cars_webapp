from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Sale, Invoice
from .forms import SaleForm, InvoiceForm, SaleSearchForm, QuickSaleForm
from inventory.models import Vehicle
from customers.models import Customer
from core.decorators import trader_required, finance_required

@login_required
def sale_list(request):
    """List all sales with search and filter capabilities"""
    
    sales = Sale.objects.select_related(
        'vehicle', 'customer', 'assigned_trader', 'assigned_trader__userprofile'
    ).prefetch_related('invoice')
    
    search_form = SaleSearchForm(request.GET)
    
    # Apply filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        if search:
            sales = sales.filter(
                Q(sale_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(vehicle__vin_chassis__icontains=search) |
                Q(vehicle__make__icontains=search) |
                Q(vehicle__model__icontains=search)
            )
        
        trader = search_form.cleaned_data.get('trader')
        if trader:
            sales = sales.filter(assigned_trader=trader)
        
        customer = search_form.cleaned_data.get('customer')
        if customer:
            sales = sales.filter(customer=customer)
        
        date_from = search_form.cleaned_data.get('date_from')
        if date_from:
            sales = sales.filter(sale_date__gte=date_from)
        
        date_to = search_form.cleaned_data.get('date_to')
        if date_to:
            sales = sales.filter(sale_date__lte=date_to)
        
        payment_method = search_form.cleaned_data.get('payment_method')
        if payment_method:
            sales = sales.filter(payment_method=payment_method)
        
        is_finalized = search_form.cleaned_data.get('is_finalized')
        if is_finalized == 'true':
            sales = sales.filter(is_finalized=True)
        elif is_finalized == 'false':
            sales = sales.filter(is_finalized=False)
    
    # Role-based filtering
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader:
            # Traders see only their own sales
            sales = sales.filter(assigned_trader=request.user)
    
    # Calculate statistics
    stats = {
        'total_sales': sales.count(),
        'total_revenue': sales.aggregate(Sum('sale_price'))['sale_price__sum'] or 0,
        'avg_sale_price': sales.aggregate(Avg('sale_price'))['sale_price__avg'] or 0,
        'total_commission': sales.aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0,
    }
    
    # Pagination
    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'stats': stats,
        'total_count': sales.count(),
    }
    
    return render(request, 'sales/list.html', context)

@trader_required
def sale_create(request):
    """Create new sale"""
    
    if request.method == 'POST':
        form = SaleForm(request.POST, user=request.user)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.created_by = request.user
            sale.save()
            
            messages.success(request, f"Vente {sale.sale_number} créée avec succès.")
            return redirect('sales:detail', pk=sale.pk)
    else:
        form = SaleForm(user=request.user)
    
    return render(request, 'sales/form.html', {
        'form': form,
        'title': 'Nouvelle Vente'
    })

@login_required
def sale_detail(request, pk):
    """Sale detail view"""
    
    sale = get_object_or_404(
        Sale.objects.select_related(
            'vehicle__vehicle_purchase__supplier',
            'customer',
            'assigned_trader__userprofile'
        ).prefetch_related('invoice'),
        pk=pk
    )
    
    # Check permissions
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader and sale.assigned_trader != request.user:
            messages.error(request, "Vous ne pouvez voir que vos propres ventes.")
            return redirect('sales:list')
    
    # Calculate detailed margins
    landed_cost = sale.landed_cost
    margin_amount = sale.margin_amount
    margin_percentage = sale.margin_percentage
    
    # Cost breakdown
    cost_breakdown = {
        'purchase_price': sale.vehicle.vehicle_purchase.purchase_price_da or 0,
        'freight_cost': 0,
        'customs_cost': 0,
    }
    
    if hasattr(sale.vehicle.vehicle_purchase, 'freight_cost'):
        cost_breakdown['freight_cost'] = sale.vehicle.vehicle_purchase.freight_cost.total_freight_cost_da or 0
    
    if hasattr(sale.vehicle.vehicle_purchase, 'customs_declaration'):
        cost_breakdown['customs_cost'] = sale.vehicle.vehicle_purchase.customs_declaration.total_customs_cost_da or 0
    
    # Check if invoice exists
    has_invoice = hasattr(sale, 'invoice')
    
    context = {
        'sale': sale,
        'landed_cost': landed_cost,
        'margin_amount': margin_amount,
        'margin_percentage': margin_percentage,
        'cost_breakdown': cost_breakdown,
        'has_invoice': has_invoice,
    }
    
    return render(request, 'sales/detail.html', context)

@trader_required
def sale_edit(request, pk):
    """Edit sale (only if not finalized)"""
    
    sale = get_object_or_404(Sale, pk=pk)
    
    # Check permissions
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader and sale.assigned_trader != request.user:
            messages.error(request, "Vous ne pouvez modifier que vos propres ventes.")
            return redirect('sales:list')
    
    # Check if sale can be edited
    if sale.is_finalized:
        messages.error(request, "Impossible de modifier une vente finalisée.")
        return redirect('sales:detail', pk=pk)
    
    if hasattr(sale, 'invoice') and sale.invoice.status != 'draft':
        messages.error(request, "Impossible de modifier une vente avec facture émise.")
        return redirect('sales:detail', pk=pk)
    
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale, user=request.user)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.updated_by = request.user
            sale.save()
            
            messages.success(request, f"Vente {sale.sale_number} modifiée avec succès.")
            return redirect('sales:detail', pk=pk)
    else:
        form = SaleForm(instance=sale, user=request.user)
    
    return render(request, 'sales/form.html', {
        'form': form,
        'sale': sale,
        'title': f'Modifier Vente {sale.sale_number}'
    })

@trader_required
def sale_create_invoice(request, pk):
    """Create invoice for sale"""
    
    sale = get_object_or_404(Sale, pk=pk)
    
    # Check permissions
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader and sale.assigned_trader != request.user:
            messages.error(request, "Vous ne pouvez créer des factures que pour vos propres ventes.")
            return redirect('sales:list')
    
    # Check if invoice already exists
    if hasattr(sale, 'invoice'):
        messages.warning(request, "Une facture existe déjà pour cette vente.")
        return redirect('sales:invoice_detail', pk=sale.invoice.pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.sale = sale
            invoice.customer = sale.customer
            invoice.created_by = request.user
            
            # Set initial payment if down payment exists
            if sale.down_payment > 0:
                invoice.amount_paid = sale.down_payment
            
            invoice.save()
            
            messages.success(request, f"Facture {invoice.invoice_number} créée avec succès.")
            return redirect('sales:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
    
    return render(request, 'sales/invoice_form.html', {
        'form': form,
        'sale': sale,
        'title': f'Créer Facture - Vente {sale.sale_number}'
    })

@login_required
def invoice_detail(request, pk):
    """Invoice detail view"""
    
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'sale__vehicle',
            'sale__assigned_trader',
            'customer'
        ),
        pk=pk
    )
    
    # Check permissions
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader and invoice.sale.assigned_trader != request.user:
            messages.error(request, "Vous ne pouvez voir que vos propres factures.")
            return redirect('sales:list')
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'sales/invoice_detail.html', context)

@login_required
def invoice_print(request, pk):
    """Print-ready invoice view"""
    
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'sale__vehicle__vehicle_purchase__supplier',
            'sale__assigned_trader',
            'customer'
        ),
        pk=pk
    )
    
    # Check permissions
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader and invoice.sale.assigned_trader != request.user:
            messages.error(request, "Accès non autorisé.")
            return redirect('sales:list')
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'sales/invoice_print.html', context)

@trader_required
def sale_finalize(request, pk):
    """Finalize sale (lock it from editing)"""
    
    if request.method == 'POST':
        sale = get_object_or_404(Sale, pk=pk)
        
        # Check permissions
        if hasattr(request.user, 'userprofile'):
            if request.user.userprofile.is_trader and sale.assigned_trader != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Vous ne pouvez finaliser que vos propres ventes.'
                })
        
        # Check if can be finalized
        if sale.is_finalized:
            return JsonResponse({
                'success': False,
                'message': 'Cette vente est déjà finalisée.'
            })
        
        sale.is_finalized = True
        sale.updated_by = request.user
        sale.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Vente {sale.sale_number} finalisée avec succès.'
        })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@login_required
def ajax_vehicle_details(request):
    """AJAX endpoint to get vehicle details for sale form"""
    
    vehicle_id = request.GET.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({'error': 'Vehicle ID required'})
    
    try:
        vehicle = Vehicle.objects.select_related(
            'vehicle_purchase__supplier'
        ).get(pk=vehicle_id)
        
        return JsonResponse({
            'success': True,
            'vehicle': {
                'vin_chassis': vehicle.vin_chassis,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year,
                'color': vehicle.color,
                'landed_cost': float(vehicle.landed_cost),
                'supplier': vehicle.vehicle_purchase.supplier.name,
            }
        })
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'})

@login_required
def ajax_calculate_margin(request):
    """AJAX endpoint to calculate sale margin"""
    
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        sale_price = request.POST.get('sale_price')
        
        if not vehicle_id or not sale_price:
            return JsonResponse({'error': 'Missing parameters'})
        
        try:
            vehicle = Vehicle.objects.get(pk=vehicle_id)
            sale_price = float(sale_price)
            
            landed_cost = vehicle.landed_cost
            margin_amount = sale_price - landed_cost
            margin_percentage = (margin_amount / landed_cost * 100) if landed_cost > 0 else 0
            
            return JsonResponse({
                'success': True,
                'landed_cost': float(landed_cost),
                'margin_amount': margin_amount,
                'margin_percentage': round(margin_percentage, 2),
                'is_profitable': margin_amount > 0
            })
        except (Vehicle.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid data'})
    
    return JsonResponse({'error': 'Invalid request'})

@trader_required
def quick_sale(request):
    """Quick sale creation (AJAX)"""
    
    if request.method == 'POST':
        form = QuickSaleForm(request.POST, user=request.user)
        if form.is_valid():
            sale = form.save()
            
            return JsonResponse({
                'success': True,
                'sale_id': sale.pk,
                'sale_number': sale.sale_number,
                'message': f'Vente {sale.sale_number} créée avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    # Return form HTML for modal
    form = QuickSaleForm(user=request.user)
    return render(request, 'sales/quick_sale_form.html', {'form': form})