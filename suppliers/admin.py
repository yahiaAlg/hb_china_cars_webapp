from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Supplier

class SupplierResource(resources.ModelResource):
    class Meta:
        model = Supplier
        fields = ('name', 'country', 'contact_person', 'phone', 'email', 'address', 'currency__code', 'payment_terms', 'is_active')
        export_order = fields

@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    resource_class = SupplierResource
    list_display = ('name', 'country', 'contact_person', 'phone', 'email', 'currency', 'is_active', 'created_at')
    list_filter = ('country', 'currency', 'is_active', 'created_at')
    search_fields = ('name', 'contact_person', 'email', 'phone')
    list_editable = ('is_active',)
    ordering = ('name',)
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'country', 'contact_person', 'currency')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Conditions Commerciales', {
            'fields': ('payment_terms', 'notes')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)