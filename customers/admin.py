from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Customer, CustomerNote

class CustomerNoteInline(admin.TabularInline):
    model = CustomerNote
    extra = 1

class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer
        fields = ('name', 'customer_type', 'nif_tax_id', 'phone', 'email', 'address', 'wilaya', 'is_active')

@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    resource_class = CustomerResource
    list_display = ('name', 'customer_type', 'phone', 'wilaya', 'is_active', 'created_at')
    list_filter = ('customer_type', 'wilaya', 'is_active', 'created_at')
    search_fields = ('name', 'phone', 'email', 'nif_tax_id')
    list_editable = ('is_active',)
    inlines = [CustomerNoteInline]
    
    fieldsets = (
        ('Informations de Base', {
            'fields': ('name', 'customer_type', 'nif_tax_id')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'address', 'wilaya')
        }),
        ('Notes et Statut', {
            'fields': ('notes', 'is_active')
        }),
    )

@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_at', 'created_by', 'is_important')
    list_filter = ('is_important', 'created_at')
    search_fields = ('customer__name', 'note')
    readonly_fields = ('created_at', 'updated_at')