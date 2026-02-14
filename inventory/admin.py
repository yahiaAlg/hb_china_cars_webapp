from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Vehicle, VehiclePhoto, StockAlert

class VehiclePhotoInline(admin.TabularInline):
    model = VehiclePhoto
    extra = 1

class VehicleResource(resources.ModelResource):
    class Meta:
        model = Vehicle
        fields = ('vin_chassis', 'make', 'model', 'year', 'color', 'status', 'vehicle_purchase__supplier__name')

@admin.register(Vehicle)
class VehicleAdmin(ImportExportModelAdmin):
    resource_class = VehicleResource
    list_display = ('vin_chassis', 'make', 'model', 'year', 'color', 'status', 'reserved_by', 'created_at')
    list_filter = ('status', 'make', 'year', 'created_at')
    search_fields = ('vin_chassis', 'make', 'model', 'color')
    list_editable = ('status',)
    inlines = [VehiclePhotoInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('vin_chassis', 'vehicle_purchase')
        }),
        ('Détails du Véhicule', {
            'fields': ('make', 'model', 'year', 'color', 'engine_type', 'specifications')
        }),
        ('Statut et Réservation', {
            'fields': ('status', 'reserved_by', 'reservation_date', 'reservation_expires')
        }),
    )
    
    readonly_fields = ('reservation_date', 'reservation_expires')

@admin.register(VehiclePhoto)
class VehiclePhotoAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'caption', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'vehicle', 'is_resolved', 'created_at', 'resolved_by')
    list_filter = ('alert_type', 'is_resolved', 'created_at')
    search_fields = ('message', 'vehicle__vin_chassis')