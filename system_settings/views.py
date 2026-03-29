from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import (
    SystemConfiguration, ExchangeRateHistory, TaxRateHistory,
    UserPreference, SystemLog
)
from .forms import (
    SystemConfigurationForm, ExchangeRateForm, TaxRateForm,
    UserPreferenceForm, ExchangeRateSearchForm, SystemLogFilterForm
)
from core.decorators import manager_required

@manager_required
def system_configuration(request):
    """System configuration management"""
    
    config = SystemConfiguration.get_current()
    
    if request.method == 'POST':
        form = SystemConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save(commit=False)
            config.updated_by = request.user
            config.save()
            
            # Log the change
            SystemLog.log(
                level='info',
                action_type='update',
                message='Configuration système mise à jour',
                user=request.user,
                request=request
            )
            
            messages.success(request, "Configuration système mise à jour avec succès.")
            return redirect('system_settings:configuration')
    else:
        form = SystemConfigurationForm(instance=config)
    
    return render(request, 'system_settings/configuration.html', {
        'form': form,
        'config': config
    })

@manager_required
def exchange_rates(request):
    """Exchange rates management"""
    
    search_form = ExchangeRateSearchForm(request.GET)
    
    # Get exchange rates
    rates = ExchangeRateHistory.objects.select_related(
        'from_currency', 'to_currency'
    )
    
    # Apply filters
    if search_form.is_valid():
        from_currency = search_form.cleaned_data.get('from_currency')
        if from_currency:
            rates = rates.filter(from_currency=from_currency)
        
        to_currency = search_form.cleaned_data.get('to_currency')
        if to_currency:
            rates = rates.filter(to_currency=to_currency)
        
        date_from = search_form.cleaned_data.get('date_from')
        if date_from:
            rates = rates.filter(effective_date__gte=date_from)
        
        date_to = search_form.cleaned_data.get('date_to')
        if date_to:
            rates = rates.filter(effective_date__lte=date_to)
    
    # Get current rates (latest for each currency pair)
    current_rates = {}
    for rate in rates:
        key = f"{rate.from_currency.code}_{rate.to_currency.code}"
        if key not in current_rates or rate.effective_date > current_rates[key].effective_date:
            current_rates[key] = rate
    
    # Pagination
    paginator = Paginator(rates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'current_rates': current_rates.values(),
        'total_count': rates.count(),
    }
    
    return render(request, 'system_settings/exchange_rates.html', context)

@manager_required
def exchange_rate_create(request):
    """Create new exchange rate"""
    
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.created_by = request.user
            rate.save()
            
            # Log the change
            SystemLog.log(
                level='info',
                action_type='create',
                message=f'Nouveau taux de change: {rate}',
                user=request.user,
                request=request
            )
            
            messages.success(request, "Taux de change enregistré avec succès.")
            return redirect('system_settings:exchange_rates')
    else:
        form = ExchangeRateForm()
    
    return render(request, 'system_settings/exchange_rate_form.html', {
        'form': form,
        'title': 'Nouveau Taux de Change'
    })

@manager_required
def exchange_rate_edit(request, pk):
    """Edit exchange rate"""
    
    rate = get_object_or_404(ExchangeRateHistory, pk=pk)
    
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST, instance=rate)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.updated_by = request.user
            rate.save()
            
            # Log the change
            SystemLog.log(
                level='info',
                action_type='update',
                message=f'Taux de change modifié: {rate}',
                user=request.user,
                request=request
            )
            
            messages.success(request, "Taux de change modifié avec succès.")
            return redirect('system_settings:exchange_rates')
    else:
        form = ExchangeRateForm(instance=rate)
    
    return render(request, 'system_settings/exchange_rate_form.html', {
        'form': form,
        'rate': rate,
        'title': f'Modifier Taux de Change'
    })

@manager_required
def tax_rates(request):
    """Tax rates management"""
    
    rates = TaxRateHistory.objects.all()
    
    # Get current rates (latest for each tax type)
    current_rates = {}
    for rate in rates:
        if rate.tax_type not in current_rates or rate.effective_date > current_rates[rate.tax_type].effective_date:
            current_rates[rate.tax_type] = rate
    
    # Pagination
    paginator = Paginator(rates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_rates': current_rates.values(),
        'total_count': rates.count(),
    }
    
    return render(request, 'system_settings/tax_rates.html', context)

@manager_required
def tax_rate_create(request):
    """Create new tax rate"""
    
    if request.method == 'POST':
        form = TaxRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.created_by = request.user
            rate.save()
            
            # Log the change
            SystemLog.log(
                level='info',
                action_type='create',
                message=f'Nouveau taux de taxe: {rate}',
                user=request.user,
                request=request
            )
            
            messages.success(request, "Taux de taxe enregistré avec succès.")
            return redirect('system_settings:tax_rates')
    else:
        form = TaxRateForm()
    
    return render(request, 'system_settings/tax_rate_form.html', {
        'form': form,
        'title': 'Nouveau Taux de Taxe'
    })

@manager_required
def tax_rate_edit(request, pk):
    """Edit tax rate"""
    
    rate = get_object_or_404(TaxRateHistory, pk=pk)
    
    if request.method == 'POST':
        form = TaxRateForm(request.POST, instance=rate)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.updated_by = request.user
            rate.save()
            
            # Log the change
            SystemLog.log(
                level='info',
                action_type='update',
                message=f'Taux de taxe modifié: {rate}',
                user=request.user,
                request=request
            )
            
            messages.success(request, "Taux de taxe modifié avec succès.")
            return redirect('system_settings:tax_rates')
    else:
        form = TaxRateForm(instance=rate)
    
    return render(request, 'system_settings/tax_rate_form.html', {
        'form': form,
        'rate': rate,
        'title': f'Modifier Taux de Taxe'
    })

@login_required
def user_preferences(request):
    """User preferences management"""
    
    # Get or create user preferences
    preferences, created = UserPreference.objects.get_or_create(
        user=request.user,
        defaults={'created_by': request.user}
    )
    
    if request.method == 'POST':
        form = UserPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            preferences = form.save(commit=False)
            preferences.updated_by = request.user
            preferences.save()
            
            messages.success(request, "Préférences mises à jour avec succès.")
            return redirect('system_settings:user_preferences')
    else:
        form = UserPreferenceForm(instance=preferences)
    
    return render(request, 'system_settings/user_preferences.html', {
        'form': form,
        'preferences': preferences
    })

@manager_required
def system_logs(request):
    """System logs viewer"""
    
    filter_form = SystemLogFilterForm(request.GET)
    
    # Get logs
    logs = SystemLog.objects.select_related('user')
    
    # Apply filters
    if filter_form.is_valid():
        level = filter_form.cleaned_data.get('level')
        if level:
            logs = logs.filter(level=level)
        
        action_type = filter_form.cleaned_data.get('action_type')
        if action_type:
            logs = logs.filter(action_type=action_type)
        
        user = filter_form.cleaned_data.get('user')
        if user:
            logs = logs.filter(user__username__icontains=user)
        
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            logs = logs.filter(created_at__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            logs = logs.filter(created_at__lte=date_to)
        
        search = filter_form.cleaned_data.get('search')
        if search:
            logs = logs.filter(message__icontains=search)
    
    # Statistics
    stats = {
        'total_logs': logs.count(),
        'error_count': logs.filter(level='error').count(),
        'warning_count': logs.filter(level='warning').count(),
        'info_count': logs.filter(level='info').count(),
    }
    
    # Recent critical logs
    critical_logs = logs.filter(level__in=['error', 'critical'])[:10]
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'stats': stats,
        'critical_logs': critical_logs,
        'total_count': logs.count(),
    }
    
    return render(request, 'system_settings/system_logs.html', context)

@manager_required
def clear_old_logs(request):
    """Clear old system logs"""
    
    if request.method == 'POST':
        days = int(request.POST.get('days', 30))
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        deleted_count, _ = SystemLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        # Log the cleanup
        SystemLog.log(
            level='info',
            action_type='system',
            message=f'Nettoyage des logs: {deleted_count} entrées supprimées',
            user=request.user,
            request=request
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} entrées de log supprimées.',
            'deleted_count': deleted_count
        })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@login_required
def ajax_latest_exchange_rate(request):
    """AJAX endpoint to get latest exchange rate"""
    
    from_currency = request.GET.get('from_currency')
    to_currency = request.GET.get('to_currency', 'DA')
    
    if not from_currency:
        return JsonResponse({'error': 'From currency required'})
    
    try:
        rate = ExchangeRateHistory.get_latest_rate(from_currency, to_currency)
        
        if rate:
            return JsonResponse({
                'success': True,
                'rate': float(rate.rate),
                'effective_date': rate.effective_date.strftime('%Y-%m-%d'),
                'source': rate.source
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Aucun taux trouvé pour {from_currency} vers {to_currency}'
            })
    
    except Exception as e:
        return JsonResponse({'error': str(e)})

@manager_required
def system_status(request):
    """System status dashboard"""
    
    # Database statistics
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM django_session")
        active_sessions = cursor.fetchone()[0]
    
    # Recent activity
    recent_logs = SystemLog.objects.select_related('user')[:10]
    
    # System configuration
    config = SystemConfiguration.get_current()
    
    # Current exchange rates
    current_rates = {}
    for currency_code in ['USD', 'CNY']:
        rate = ExchangeRateHistory.get_latest_rate(currency_code, 'DA')
        if rate:
            current_rates[currency_code] = rate
    
    context = {
        'active_sessions': active_sessions,
        'recent_logs': recent_logs,
        'config': config,
        'current_rates': current_rates,
    }
    
    return render(request, 'system_settings/system_status.html', context)