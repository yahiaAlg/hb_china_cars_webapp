from django.contrib import admin
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from .models import Sale, SaleLineItem, Invoice


# ── Inlines ───────────────────────────────────────────────────────────────────


class SaleLineItemInline(admin.TabularInline):
    model = SaleLineItem
    extra = 0
    fields = ("line_number", "vehicle", "sale_price", "notes")
    readonly_fields = ("line_number",)
    raw_id_fields = ("vehicle",)


class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 0
    readonly_fields = (
        "invoice_number",
        "subtotal_ht",
        "tva_amount",
        "total_ttc",
        "balance_due",
    )


# ── Sale ──────────────────────────────────────────────────────────────────────


@admin.register(Sale)
class SaleAdmin(ImportExportModelAdmin):

    list_display = (
        "sale_number",
        "sale_date",
        "customer",
        "assigned_trader",
        "vehicle_count_display",
        "sale_price_display",
        "commission_amount",
        "is_finalized",
        "created_at",
    )
    list_filter = (
        "sale_date",
        "assigned_trader",
        "payment_method",
        "is_finalized",
        "created_at",
    )
    search_fields = (
        "sale_number",
        "customer__name",
        "line_items__vehicle__vin_chassis",
        "line_items__vehicle__make",
        "line_items__vehicle__model",
    )
    readonly_fields = (
        "sale_number",
        "commission_amount",
        "margin_amount_display",
        "margin_percentage_display",
        "sale_price_display",
        "vehicle_count_display",
    )
    inlines = [SaleLineItemInline, InvoiceInline]

    fieldsets = (
        (
            "Informations de Vente",
            {
                "fields": (
                    "sale_number",
                    "sale_date",
                    "customer",
                    "assigned_trader",
                    "vehicle_count_display",
                ),
            },
        ),
        (
            "Détails Financiers",
            {
                "fields": (
                    "sale_price_display",
                    "payment_method",
                    "down_payment",
                ),
            },
        ),
        (
            "Commission",
            {
                "fields": ("commission_rate", "commission_amount"),
            },
        ),
        (
            "Marges",
            {
                "fields": ("margin_amount_display", "margin_percentage_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "Statut et Notes",
            {
                "fields": ("is_finalized", "notes"),
            },
        ),
    )

    def vehicle_count_display(self, obj):
        return obj.vehicle_count

    vehicle_count_display.short_description = "Nb. véhicules"

    def sale_price_display(self, obj):
        return f"{obj.sale_price:,.2f} DA"

    sale_price_display.short_description = "Prix de vente (DA)"

    def margin_amount_display(self, obj):
        return f"{obj.margin_amount:,.2f} DA"

    margin_amount_display.short_description = "Marge (DA)"

    def margin_percentage_display(self, obj):
        return f"{obj.margin_percentage:.2f}%"

    margin_percentage_display.short_description = "Marge (%)"


# ── SaleLineItem ──────────────────────────────────────────────────────────────


@admin.register(SaleLineItem)
class SaleLineItemAdmin(admin.ModelAdmin):
    list_display = (
        "sale",
        "line_number",
        "vehicle",
        "sale_price",
        "margin_amount",
    )
    list_filter = ("sale__sale_date", "sale__assigned_trader")
    search_fields = (
        "sale__sale_number",
        "vehicle__vin_chassis",
        "vehicle__make",
        "vehicle__model",
    )
    raw_id_fields = ("vehicle", "sale")
    readonly_fields = ("line_number", "margin_amount", "margin_percentage")

    def margin_amount(self, obj):
        return f"{obj.margin_amount:,.2f} DA"

    margin_amount.short_description = "Marge (DA)"

    def margin_percentage(self, obj):
        return f"{obj.margin_percentage:.2f}%"

    margin_percentage.short_description = "Marge (%)"


# ── Invoice ───────────────────────────────────────────────────────────────────


class InvoiceResource(resources.ModelResource):
    class Meta:
        model = Invoice
        fields = (
            "invoice_number",
            "invoice_date",
            "customer__name",
            "sale__sale_number",
            "total_ttc",
            "amount_paid",
            "balance_due",
            "status",
        )


@admin.register(Invoice)
class InvoiceAdmin(ImportExportModelAdmin):
    resource_class = InvoiceResource
    list_display = (
        "invoice_number",
        "invoice_date",
        "customer",
        "total_ttc",
        "amount_paid",
        "balance_due",
        "status",
        "is_overdue_display",
    )
    list_filter = ("status", "invoice_date", "due_date", "created_at")
    search_fields = ("invoice_number", "customer__name", "sale__sale_number")
    readonly_fields = (
        "invoice_number",
        "subtotal_ht",
        "tva_amount",
        "total_ttc",
        "balance_due",
        "is_overdue_display",
        "days_overdue_display",
    )

    fieldsets = (
        (
            "Informations de Facture",
            {
                "fields": (
                    "invoice_number",
                    "invoice_date",
                    "due_date",
                    "sale",
                    "customer",
                ),
            },
        ),
        (
            "Calculs Fiscaux",
            {
                "fields": ("subtotal_ht", "tva_rate", "tva_amount", "total_ttc"),
            },
        ),
        (
            "Paiements",
            {
                "fields": ("amount_paid", "balance_due", "status"),
            },
        ),
        (
            "Informations Complémentaires",
            {
                "fields": ("is_overdue_display", "days_overdue_display", "notes"),
                "classes": ("collapse",),
            },
        ),
    )

    def is_overdue_display(self, obj):
        return obj.is_overdue

    is_overdue_display.boolean = True
    is_overdue_display.short_description = "En retard"

    def days_overdue_display(self, obj):
        return f"{obj.days_overdue} jours" if obj.days_overdue > 0 else "-"

    days_overdue_display.short_description = "Jours de retard"
