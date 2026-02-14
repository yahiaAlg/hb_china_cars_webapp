from django.contrib import admin
from .models import ReportTemplate, ScheduledReport, ReportExecution

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'report_type', 'is_public', 'usage_count', 
        'last_used', 'created_at'
    )
    list_filter = ('report_type', 'is_public', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('usage_count', 'last_used')
    
    fieldsets = (
        ('Rapport', {
            'fields': ('name', 'report_type', 'description')
        }),
        ('Paramètres', {
            'fields': ('filter_parameters',)
        }),
        ('Accès', {
            'fields': ('is_public', 'allowed_roles')
        }),
        ('Utilisation', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'template', 'frequency', 'next_run', 
        'last_run', 'status'
    )
    list_filter = ('frequency', 'status', 'next_run')
    search_fields = ('name', 'template__name')
    filter_horizontal = ('recipients',)
    
    fieldsets = (
        ('Rapport Planifié', {
            'fields': ('name', 'template', 'frequency')
        }),
        ('Destinataires', {
            'fields': ('recipients', 'email_subject')
        }),
        ('Planification', {
            'fields': ('next_run', 'last_run', 'status')
        }),
    )

@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = (
        'template', 'executed_by', 'start_time', 'end_time',
        'status', 'record_count', 'duration'
    )
    list_filter = ('status', 'start_time', 'template__report_type')
    search_fields = ('template__name', 'executed_by__username')
    readonly_fields = ('duration',)
    
    fieldsets = (
        ('Exécution', {
            'fields': ('template', 'executed_by', 'start_time', 'end_time', 'status')
        }),
        ('Résultats', {
            'fields': ('record_count', 'file_path', 'duration')
        }),
        ('Erreurs', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def duration(self, obj):
        if obj.duration:
            return str(obj.duration)
        return "-"
    duration.short_description = "Durée"