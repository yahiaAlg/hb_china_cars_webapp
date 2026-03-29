from django.contrib import admin
from .models import (
    SystemConfiguration, ExchangeRateHistory, TaxRateHistory,
    UserPreference, SystemLog, BackupConfiguration
)

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'default_tva_rate', 'default_tariff_rate',
        'default_commission_rate', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations de l\'Entreprise', {
            'fields': (
                'company_name', 'company_nif', 'company_address',
                'company_phone', 'company_email'
            )
        }),
        ('Taux par Défaut', {
            'fields': (
                'default_tva_rate', 'default_tariff_rate', 'default_commission_rate'
            )
        }),
        ('Paramètres Système', {
            'fields': (
                'reservation_duration_days', 'invoice_due_days'
            )
        }),
        ('Notifications', {
            'fields': (
                'enable_email_notifications', 'enable_overdue_alerts',
                'overdue_alert_days'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ExchangeRateHistory)
class ExchangeRateHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'from_currency', 'to_currency', 'rate',
        'effective_date', 'source', 'created_at'
    )
    list_filter = ('from_currency', 'to_currency', 'effective_date')
    search_fields = ('source', 'notes')
    ordering = ('-effective_date', 'from_currency')
    
    fieldsets = (
        ('Taux de Change', {
            'fields': ('from_currency', 'to_currency', 'rate', 'effective_date')
        }),
        ('Informations', {
            'fields': ('source', 'notes')
        }),
    )

@admin.register(TaxRateHistory)
class TaxRateHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'tax_type', 'rate', 'effective_date', 'description', 'created_at'
    )
    list_filter = ('tax_type', 'effective_date')
    search_fields = ('description',)
    ordering = ('-effective_date', 'tax_type')

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'theme', 'language', 'default_page_size',
        'email_notifications', 'updated_at'
    )
    list_filter = ('theme', 'language', 'email_notifications')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Affichage', {
            'fields': ('theme', 'language', 'default_page_size')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'browser_notifications')
        }),
        ('Rapports', {
            'fields': ('default_export_format',)
        }),
    )

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = (
        'level', 'action_type', 'user', 'message_short',
        'ip_address', 'created_at'
    )
    list_filter = ('level', 'action_type', 'created_at')
    search_fields = ('message', 'user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'
    
    fieldsets = (
        ('Log Entry', {
            'fields': ('level', 'action_type', 'user', 'message')
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

@admin.register(BackupConfiguration)
class BackupConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'backup_type', 'frequency', 'next_backup',
        'last_backup', 'is_active'
    )
    list_filter = ('backup_type', 'frequency', 'is_active')
    search_fields = ('name',)
    
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'backup_type', 'frequency', 'is_active')
        }),
        ('Stockage', {
            'fields': ('storage_path', 'max_backups_to_keep')
        }),
        ('Planification', {
            'fields': ('next_backup', 'last_backup')
        }),
    )