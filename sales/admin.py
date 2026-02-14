from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Sale, Invoice

class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 0
    readonly_fields = ('invoice_number', 'subtotal_ht', 'tva_amount', 'total_ttc', 'balance_due')

class SaleResource(resources.ModelResource):
    class Meta:
        model = Sale
        fields = (
            'sale_number', 'sale_date', 'vehicle__vin_chassis', 'customer__name',
            'assigned_trader__username', 'sale_price', 'commission_amount', 'is_finalized'
        )

@admin.register(Sale)
class SaleAdmin(ImportExportModelAdmin):
    resource_class = SaleResource
    list_display = (
        'sale_number', 'sale_date', 'vehicle', 'customer', 'assigned_trader',
        'sale_price', 'commission_amount', 'is_finalized', 'created_at'
    )
    list_filter = ('sale_date', 'assigned_trader', 'payment_method', 'is_finalized', 'created_at')
    search_fields = ('sale_number', 'vehicle__vin_chassis', 'customer__name')
    readonly_fields = ('sale_number', 'commission_amount', 'margin_amount', 'margin_percentage')
    inlines = [InvoiceInline]
    
    fieldsets = (
        ('Informations de Vente', {
            'fields': ('sale_number', 'sale_date', 'vehicle', 'customer', 'assigned_trader')
        }),
        ('Détails Financiers', {
            'fields': ('sale_price', 'payment_method', 'down_payment')
        }),
        ('Commission', {
            'fields': ('commission_rate', 'commission_amount')
        }),
        ('Marges', {
            'fields': ('margin_amount', 'margin_percentage'),
            'classes': ('collapse',)
        }),
        ('Statut et Notes', {
            'fields': ('is_finalized', 'notes')
        }),
    )
    
    def margin_amount(self, obj):
        return f"{obj.margin_amount:,.2f} DA"
    margin_amount.short_description = "Marge (DA)"
    
    def margin_percentage(self, obj):
        return f"{obj.margin_percentage:.2f}%"
    margin_percentage.short_description = "Marge (%)"

class InvoiceResource(resources.ModelResource):
    class Meta:
        model = Invoice
        fields = (
            'invoice_number', 'invoice_date', 'customer__name', 'sale__sale_number',
            'total_ttc', 'amount_paid', 'balance_due', 'status'
        )

@admin.register(Invoice)
class InvoiceAdmin(ImportExportModelAdmin):
    resource_class = InvoiceResource
    list_display = (
        'invoice_number', 'invoice_date', 'customer', 'total_ttc',
        'amount_paid', 'balance_due', 'status', 'is_overdue'
    )
    list_filter = ('status', 'invoice_date', 'due_date', 'created_at')
    search_fields = ('invoice_number', 'customer__name', 'sale__sale_number')
    readonly_fields = (
        'invoice_number', 'subtotal_ht', 'tva_amount', 'total_ttc',
        'balance_due', 'is_overdue', 'days_overdue'
    )
    
    fieldsets = (
        ('Informations de Facture', {
            'fields': ('invoice_number', 'invoice_date', 'due_date', 'sale', 'customer')
        }),
        ('Calculs Fiscaux', {
            'fields': ('subtotal_ht', 'tva_rate', 'tva_amount', 'total_ttc')
        }),
        ('Paiements', {
            'fields': ('amount_paid', 'balance_due', 'status')
        }),
        ('Informations Complémentaires', {
            'fields': ('is_overdue', 'days_overdue', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = "En retard"
    
    def days_overdue(self, obj):
        return f"{obj.days_overdue} jours" if obj.days_overdue > 0 else "-"
    days_overdue.short_description = "Jours de retard"