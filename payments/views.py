from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Payment, PaymentReminder, PaymentPlan, Installment
from .forms import (
    PaymentForm, QuickPaymentForm, PaymentSearchForm, PaymentReminderForm,
    PaymentPlanForm, OutstandingInvoicesFilterForm
)
from sales.models import Invoice
from core.decorators import finance_required

@login_required
def payment_list(request):
    """List all payments with search and filter capabilities"""
    
    payments = Payment.objects.select_related(
        'invoice__customer', 'invoice__sale__assigned_trader'
    )
    
    search_form = PaymentSearchForm(request.GET)
    
    # Apply filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        if search:
            payments = payments.filter(
                Q(payment_number__icontains=search) |
                Q(invoice__invoice_number__icontains=search) |
                Q(invoice__customer__name__icontains=search) |
                Q(bank_reference__icontains=search)
            )
        
        customer = search_form.cleaned_data.get('customer')
        if customer:
            payments = payments.filter(
                invoice__customer__name__icontains=customer
            )
        
        payment_method = search_form.cleaned_data.get('payment_method')
        if payment_method:
            payments = payments.filter(payment_method=payment_method)
        
        date_from = search_form.cleaned_data.get('date_from')
        if date_from:
            payments = payments.filter(payment_date__gte=date_from)
        
        date_to = search_form.cleaned_data.get('date_to')
        if date_to:
            payments = payments.filter(payment_date__lte=date_to)
        
        amount_min = search_form.cleaned_data.get('amount_min')
        if amount_min:
            payments = payments.filter(amount__gte=amount_min)
        
        amount_max = search_form.cleaned_data.get('amount_max')
        if amount_max:
            payments = payments.filter(amount__lte=amount_max)
    
    # Role-based filtering
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader:
            # Traders see only payments for their sales
            payments = payments.filter(
                invoice__sale__assigned_trader=request.user
            )
    
    # Calculate statistics
    stats = {
        'total_payments': payments.count(),
        'total_amount': payments.aggregate(Sum('amount'))['amount__sum'] or 0,
        'avg_payment': payments.aggregate(Avg('amount'))['amount__avg'] or 0,
    }
    
    # Recent payments (last 7 days)
    week_ago = timezone.now().date() - timedelta(days=7)
    recent_payments = payments.filter(payment_date__gte=week_ago)
    stats['recent_count'] = recent_payments.count()
    stats['recent_amount'] = recent_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'stats': stats,
        'total_count': payments.count(),
    }
    
    return render(request, 'payments/list.html', context)

@finance_required
def payment_create(request):
    """Create new payment"""
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()
            
            messages.success(request, f"Paiement {payment.payment_number} enregistré avec succès.")
            return redirect('payments:detail', pk=payment.pk)
    else:
        form = PaymentForm()
        
        # Pre-select invoice if provided in URL
        invoice_id = request.GET.get('invoice')
        if invoice_id:
            try:
                invoice = Invoice.objects.get(pk=invoice_id)
                form.fields['invoice'].initial = invoice
                form.fields['amount'].initial = invoice.balance_due
            except Invoice.DoesNotExist:
                pass
    
    return render(request, 'payments/form.html', {
        'form': form,
        'title': 'Nouveau Paiement'
    })

@login_required
def payment_detail(request, pk):
    """Payment detail view"""
    
    payment = get_object_or_404(
        Payment.objects.select_related(
            'invoice__customer',
            'invoice__sale__vehicle',
            'invoice__sale__assigned_trader'
        ),
        pk=pk
    )
    
    # Check permissions
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader:
            if payment.invoice.sale.assigned_trader != request.user:
                messages.error(request, "Vous ne pouvez voir que les paiements de vos propres ventes.")
                return redirect('payments:list')
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/detail.html', context)

@finance_required
def payment_edit(request, pk):
    """Edit payment"""
    
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.updated_by = request.user
            payment.save()
            
            messages.success(request, f"Paiement {payment.payment_number} modifié avec succès.")
            return redirect('payments:detail', pk=payment.pk)
    else:
        form = PaymentForm(instance=payment)
    
    return render(request, 'payments/form.html', {
        'form': form,
        'payment': payment,
        'title': f'Modifier Paiement {payment.payment_number}'
    })

@login_required
def outstanding_invoices(request):
    """Outstanding invoices report"""
    
    invoices = Invoice.objects.filter(
        balance_due__gt=0
    ).select_related(
        'customer', 'sale__assigned_trader', 'sale__vehicle'
    ).prefetch_related('payments')
    
    filter_form = OutstandingInvoicesFilterForm(request.GET)
    
    # Apply filters
    if filter_form.is_valid():
        customer = filter_form.cleaned_data.get('customer')
        if customer:
            invoices = invoices.filter(customer__name__icontains=customer)
        
        trader = filter_form.cleaned_data.get('trader')
        if trader:
            invoices = invoices.filter(sale__assigned_trader=trader)
        
        overdue_only = filter_form.cleaned_data.get('overdue_only')
        if overdue_only:
            invoices = invoices.filter(due_date__lt=timezone.now().date())
        
        days_overdue_min = filter_form.cleaned_data.get('days_overdue_min')
        if days_overdue_min:
            cutoff_date = timezone.now().date() - timedelta(days=days_overdue_min)
            invoices = invoices.filter(due_date__lt=cutoff_date)
        
        amount_min = filter_form.cleaned_data.get('amount_min')
        if amount_min:
            invoices = invoices.filter(balance_due__gte=amount_min)
    
    # Role-based filtering
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader:
            invoices = invoices.filter(sale__assigned_trader=request.user)
    
    # Calculate statistics
    total_outstanding = invoices.aggregate(Sum('balance_due'))['balance_due__sum'] or 0
    overdue_invoices = invoices.filter(due_date__lt=timezone.now().date())
    total_overdue = overdue_invoices.aggregate(Sum('balance_due'))['balance_due__sum'] or 0
    
    stats = {
        'total_invoices': invoices.count(),
        'total_outstanding': total_outstanding,
        'overdue_count': overdue_invoices.count(),
        'total_overdue': total_overdue,
        'avg_outstanding': total_outstanding / invoices.count() if invoices.count() > 0 else 0,
    }
    
    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'stats': stats,
        'total_count': invoices.count(),
    }
    
    return render(request, 'payments/outstanding.html', context)

@finance_required
def quick_payment(request, invoice_id):
    """Quick payment entry for specific invoice"""
    
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        form = QuickPaymentForm(request.POST, invoice=invoice)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()
            
            return JsonResponse({
                'success': True,
                'payment_id': payment.pk,
                'payment_number': payment.payment_number,
                'new_balance': float(invoice.balance_due),
                'message': f'Paiement {payment.payment_number} enregistré.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    # Return form HTML for modal
    form = QuickPaymentForm(invoice=invoice)
    return render(request, 'payments/quick_payment_form.html', {
        'form': form,
        'invoice': invoice
    })

@finance_required
def payment_reminder_create(request, invoice_id):
    """Create payment reminder for invoice"""
    
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        form = PaymentReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.invoice = invoice
            reminder.sent_by = request.user
            reminder.created_by = request.user
            reminder.save()
            
            messages.success(request, "Relance de paiement enregistrée avec succès.")
            return redirect('payments:outstanding')
    else:
        form = PaymentReminderForm()
    
    return render(request, 'payments/reminder_form.html', {
        'form': form,
        'invoice': invoice,
        'title': f'Relance - Facture {invoice.invoice_number}'
    })

@finance_required
def payment_plan_create(request, invoice_id):
    """Create payment plan for invoice"""
    
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    # Check if payment plan already exists
    if hasattr(invoice, 'payment_plan'):
        messages.warning(request, "Un plan de paiement existe déjà pour cette facture.")
        return redirect('payments:payment_plan_detail', pk=invoice.payment_plan.pk)
    
    if request.method == 'POST':
        form = PaymentPlanForm(request.POST, invoice=invoice)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.save()
            
            messages.success(request, f"Plan de paiement créé avec {plan.number_of_installments} échéances.")
            return redirect('payments:payment_plan_detail', pk=plan.pk)
    else:
        form = PaymentPlanForm(invoice=invoice)
    
    return render(request, 'payments/payment_plan_form.html', {
        'form': form,
        'invoice': invoice,
        'title': f'Plan de Paiement - Facture {invoice.invoice_number}'
    })

@login_required
def payment_plan_detail(request, pk):
    """Payment plan detail with installments"""
    
    plan = get_object_or_404(
        PaymentPlan.objects.select_related(
            'invoice__customer', 'invoice__sale__assigned_trader'
        ).prefetch_related('installments'),
        pk=pk
    )
    
    # Check permissions
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_trader:
            if plan.invoice.sale.assigned_trader != request.user:
                messages.error(request, "Accès non autorisé.")
                return redirect('payments:list')
    
    # Calculate plan statistics
    installments = plan.installments.all()
    paid_installments = installments.filter(status='paid')
    overdue_installments = installments.filter(status='overdue')
    
    stats = {
        'total_installments': installments.count(),
        'paid_count': paid_installments.count(),
        'overdue_count': overdue_installments.count(),
        'total_paid': sum(i.amount_paid for i in installments),
        'total_remaining': sum(i.balance_due for i in installments),
        'completion_percentage': (paid_installments.count() / installments.count() * 100) if installments.count() > 0 else 0,
    }
    
    context = {
        'plan': plan,
        'installments': installments,
        'stats': stats,
    }
    
    return render(request, 'payments/payment_plan_detail.html', context)

@finance_required
def installment_payment(request, installment_id):
    """Record payment for specific installment"""
    
    installment = get_object_or_404(Installment, pk=installment_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'cash')
        
        try:
            amount = float(amount)
            if amount <= 0 or amount > installment.balance_due:
                return JsonResponse({
                    'success': False,
                    'message': 'Montant invalide.'
                })
            
            # Update installment
            installment.amount_paid += amount
            installment.updated_by = request.user
            installment.save()
            
            # Create payment record
            Payment.objects.create(
                invoice=installment.payment_plan.invoice,
                amount=amount,
                payment_method=payment_method,
                payment_date=timezone.now().date(),
                notes=f"Paiement échéance {installment.installment_number}",
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'new_balance': float(installment.balance_due),
                'status': installment.status,
                'message': f'Paiement de {amount:,.2f} DA enregistré.'
            })
            
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Montant invalide.'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@login_required
def ajax_invoice_balance(request):
    """AJAX endpoint to get invoice balance"""
    
    invoice_id = request.GET.get('invoice_id')
    if not invoice_id:
        return JsonResponse({'error': 'Invoice ID required'})
    
    try:
        invoice = Invoice.objects.get(pk=invoice_id)
        return JsonResponse({
            'success': True,
            'balance_due': float(invoice.balance_due),
            'total_ttc': float(invoice.total_ttc),
            'amount_paid': float(invoice.amount_paid),
            'customer_name': invoice.customer.name,
            'invoice_number': invoice.invoice_number,
        })
    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'})