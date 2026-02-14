from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Purchase, FreightCost, CustomsDeclaration

class FreightCostInline(admin.StackedInline):
    model = FreightCost
    extra = 0

class CustomsDeclarationInline(admin.StackedInline):
    model = CustomsDeclaration
    extra = 0

class PurchaseResource(resources.ModelResource):
    class Meta:
        model = Purchase
        fields = ('purchase_date', 'supplier__name', 'purchase_price_fob', 'currency__code', 'exchange_rate_to_da', 'purchase_price_da')

@admin.register(Purchase)
class PurchaseAdmin(ImportExportModelAdmin):
    resource_class = PurchaseResource
    list_display = ('purchase_date', 'supplier', 'purchase_price_fob', 'currency', 'purchase_price_da', 'created_at')
    list_filter = ('purchase_date', 'supplier', 'currency', 'created_at')
    search_fields = ('supplier__name', 'notes')
    inlines = [FreightCostInline, CustomsDeclarationInline]
    
    fieldsets = (
        ('Informations d\'Achat', {
            'fields': ('purchase_date', 'supplier')
        }),
        ('Prix et Devise', {
            'fields': ('purchase_price_fob', 'currency', 'exchange_rate_to_da', 'purchase_price_da')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ('purchase_price_da',)

@admin.register(FreightCost)
class FreightCostAdmin(admin.ModelAdmin):
    list_display = ('purchase', 'freight_method', 'freight_cost', 'freight_currency', 'total_freight_cost_da')
    list_filter = ('freight_method', 'freight_currency')
    
@admin.register(CustomsDeclaration)
class CustomsDeclarationAdmin(admin.ModelAdmin):
    list_display = ('declaration_number', 'purchase', 'declaration_date', 'is_cleared', 'clearance_date', 'total_customs_cost_da')
    list_filter = ('is_cleared', 'declaration_date', 'clearance_date')
    search_fields = ('declaration_number', 'purchase__supplier__name')