from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, CustomerNote


class CustomerNoteInline(admin.TabularInline):
    model = CustomerNote
    extra = 0
    readonly_fields = ("created_at", "created_by")
    fields = ("note", "is_important", "created_by", "created_at")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "photo_thumb",
        "name",
        "customer_type",
        "phone",
        "wilaya",
        "is_active",
        "has_passport",
        "total_purchases",
    )
    list_display_links = ("photo_thumb", "name")
    list_filter = ("customer_type", "wilaya", "is_active")
    search_fields = ("name", "phone", "email", "nif_tax_id")
    readonly_fields = (
        "photo_preview",
        "passport_preview",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    inlines = [CustomerNoteInline]

    fieldsets = (
        (
            "Identité",
            {
                "fields": ("name", "customer_type", "nif_tax_id", "is_active"),
            },
        ),
        (
            "Contact",
            {
                "fields": ("phone", "email", "address", "wilaya"),
            },
        ),
        (
            "Documents",
            {
                "fields": (
                    "profile_photo",
                    "photo_preview",
                    "passport_document",
                    "passport_preview",
                ),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def photo_thumb(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;" />',
                obj.profile_photo.url,
            )
        initials = obj.name[:1].upper()
        color = "#0284c7" if obj.customer_type == "company" else "#0d9488"
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:{};color:#fff;'
            'display:flex;align-items:center;justify-content:center;font-weight:700;">{}</div>',
            color,
            initials,
        )

    photo_thumb.short_description = ""

    def photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:8px;" />',
                obj.profile_photo.url,
            )
        return "—"

    photo_preview.short_description = "Aperçu photo"

    def passport_preview(self, obj):
        if not obj.passport_document:
            return "—"
        if obj.passport_is_pdf:
            return format_html(
                '<a href="{}" target="_blank">📄 Voir le PDF</a>',
                obj.passport_document.url,
            )
        return format_html(
            '<img src="{}" style="max-height:120px;border-radius:8px;" />',
            obj.passport_document.url,
        )

    passport_preview.short_description = "Aperçu passeport"

    def has_passport(self, obj):
        return bool(obj.passport_document)

    has_passport.boolean = True
    has_passport.short_description = "Passeport"

    def total_purchases(self, obj):
        return obj.sale_set.count()

    total_purchases.short_description = "Achats"


@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "note_preview",
        "is_important",
        "created_at",
        "created_by",
    )
    list_filter = ("is_important",)
    search_fields = ("customer__name", "note")
    readonly_fields = ("created_at", "created_by")

    def note_preview(self, obj):
        return obj.note[:60] + ("…" if len(obj.note) > 60 else "")

    note_preview.short_description = "Note"
