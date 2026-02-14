from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Payment, PaymentReminder, PaymentPlan, Installment

class PaymentResource(resources.ModelResource):
    class Meta:
        model = Payment
        fields = (
            'payment_number', 'payment_date', 'invoice__invoice_number',
            'invoice__customer__name', 'amount', 'payment_method', 'is_confirmed'
        )

@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    resource_class = PaymentResource
    list_display = (
        'payment_number', 'payment_date', 'invoice', 'amount',
        'payment_method', 'is_confirmed', 'created_at'
    )
    list_filter = ('payment_method', 'is_confirmed', 'payment_date', 'created_at')
    search_fields = ('payment_number', 'invoice__invoice_number', 'invoice__customer__name')
    readonly_fields = ('payment_number',)
    
    fieldsets = (
        ('Informations de Paiement', {
            'fields': ('payment_number', 'payment_date', 'invoice', 'amount')
        }),
        ('Détails', {
            'fields': ('payment_method', 'bank_reference', 'is_confirmed')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = (
        'invoice', 'reminder_date', 'reminder_type', 'sent_by', 'follow_up_date'
    )
    list_filter = ('reminder_type', 'reminder_date', 'follow_up_date')
    search_fields = ('invoice__invoice_number', 'invoice__customer__name')
    
    fieldsets = (
        ('Relance', {
            'fields': ('invoice', 'reminder_date', 'reminder_type', 'sent_by')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Suivi', {
            'fields': ('customer_response', 'follow_up_date')
        }),
    )

class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    readonly_fields = ('balance_due', 'status')

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = (
        'invoice', 'total_amount', 'number_of_installments',
        'installment_amount', 'start_date', 'status'
    )
    list_filter = ('status', 'start_date', 'number_of_installments')
    search_fields = ('invoice__invoice_number', 'invoice__customer__name')
    readonly_fields = ('remaining_amount', 'installment_amount')
    inlines = [InstallmentInline]
    
    fieldsets = (
        ('Plan de Paiement', {
            'fields': ('invoice', 'total_amount', 'down_payment', 'remaining_amount')
        }),
        ('Échéancier', {
            'fields': ('number_of_installments', 'installment_amount', 'start_date')
        }),
        ('Statut', {
            'fields': ('status', 'notes')
        }),
    )

@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_plan', 'installment_number', 'due_date', 'amount',
        'amount_paid', 'balance_due', 'status', 'is_overdue'
    )
    list_filter = ('status', 'due_date', 'payment_date')
    search_fields = ('payment_plan__invoice__invoice_number',)
    readonly_fields = ('balance_due', 'is_overdue', 'days_overdue')
    
    fieldsets = (
        ('Échéance', {
            'fields': ('payment_plan', 'installment_number', 'due_date', 'amount')
        }),
        ('Paiement', {
            'fields': ('amount_paid', 'balance_due', 'payment_date', 'status')
        }),
        ('Statut', {
            'fields': ('is_overdue', 'days_overdue'),
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