from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import (
    CommissionTier, CommissionPeriod, CommissionSummary,
    CommissionAdjustment, CommissionPayment
)

@admin.register(CommissionTier)
class CommissionTierAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'min_sales_count', 'max_sales_count',
        'commission_rate', 'is_active', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Niveau de Commission', {
            'fields': ('name', 'commission_rate', 'is_active')
        }),
        ('Critères de Ventes', {
            'fields': ('min_sales_count', 'max_sales_count')
        }),
    )

@admin.register(CommissionPeriod)
class CommissionPeriodAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'is_closed', 'closed_date', 'closed_by')
    list_filter = ('is_closed', 'year', 'month')
    readonly_fields = ('closed_date', 'closed_by')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_closed:
            return self.readonly_fields + ('year', 'month')
        return self.readonly_fields

class CommissionSummaryResource(resources.ModelResource):
    class Meta:
        model = CommissionSummary
        fields = (
            'trader__username', 'period__year', 'period__month',
            'sales_count', 'total_commission', 'payout_status'
        )

@admin.register(CommissionSummary)
class CommissionSummaryAdmin(ImportExportModelAdmin):
    resource_class = CommissionSummaryResource
    list_display = (
        'trader', 'period', 'sales_count', 'total_commission',
        'payout_status', 'payout_date'
    )
    list_filter = ('payout_status', 'period__year', 'period__month')
    search_fields = ('trader__username', 'trader__first_name', 'trader__last_name')
    readonly_fields = ('average_commission_rate', 'average_sale_value')
    
    fieldsets = (
        ('Période et Trader', {
            'fields': ('trader', 'period')
        }),
        ('Performance', {
            'fields': ('sales_count', 'total_sales_value', 'total_margin')
        }),
        ('Commission', {
            'fields': ('base_commission', 'tier_bonus', 'total_commission')
        }),
        ('Statistiques', {
            'fields': ('average_commission_rate', 'average_sale_value'),
            'classes': ('collapse',)
        }),
        ('Paiement', {
            'fields': ('payout_status', 'payout_date', 'payout_reference')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

@admin.register(CommissionAdjustment)
class CommissionAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        'trader', 'period', 'adjustment_type', 'amount',
        'approved_by', 'created_at'
    )
    list_filter = ('adjustment_type', 'period__year', 'period__month')
    search_fields = ('trader__username', 'reason')
    
    fieldsets = (
        ('Ajustement', {
            'fields': ('trader', 'period', 'adjustment_type', 'amount')
        }),
        ('Justification', {
            'fields': ('reason', 'approved_by')
        }),
    )

@admin.register(CommissionPayment)
class CommissionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'summary', 'payment_date', 'amount_paid',
        'payment_method', 'paid_by'
    )
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('summary__trader__username', 'bank_reference')
    
    fieldsets = (
        ('Paiement', {
            'fields': ('summary', 'payment_date', 'amount_paid', 'payment_method')
        }),
        ('Références', {
            'fields': ('bank_reference', 'paid_by')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )