"""
Management command: seed_db
Usage: python manage.py seed_db

Creates the minimum required data to bootstrap the app:
  - Currencies (DA, USD, CNY)
  - Default superuser (admin / admin123)
  - SystemConfiguration (pk=1)
  - Default TVA + Tariff tax rate history entries

═══════════════════════════════════════════════════════════════════
  ALGERIAN TAX RATES — RESEARCH NOTES (verified March 2026)
═══════════════════════════════════════════════════════════════════
  TVA (VAT):      19%  — standard rate, fixed for ALL vehicle imports.
                         The 9% reduced rate applies only to basic
                         foodstuffs and tourism services, NOT vehicles.

  Customs tariff: 30%  — vehicles from China fall at the 30% ceiling
                         (range is 15–30% by category/displacement).
                         As of July 2025, tariffs on Chinese cars are
                         calculated on the original Chinese invoice
                         price (not inflated Argus values), which
                         reduces the effective duty by up to 40%,
                         but the statutory rate stays 30%.

  Commission:      4%  — company default (per business requirement).
═══════════════════════════════════════════════════════════════════
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed the database with minimum required data"

    def handle(self, *args, **options):
        self.seed_currencies()
        self.seed_superuser()
        self.seed_system_config()
        self.seed_tax_rates()
        self.stdout.write(self.style.SUCCESS("✓ Database seeded successfully."))

    # ------------------------------------------------------------------
    def seed_currencies(self):
        from core.models import Currency

        currencies = [
            {"code": "DA", "name": "Dinar Algérien", "symbol": "DA"},
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "CNY", "name": "Yuan Chinois", "symbol": "¥"},
        ]
        for c in currencies:
            obj, created = Currency.objects.get_or_create(
                code=c["code"],
                defaults={"name": c["name"], "symbol": c["symbol"], "is_active": True},
            )
            self.stdout.write(
                f"  Currency {obj.code}: {'created' if created else 'exists'}"
            )

    # ------------------------------------------------------------------
    def seed_superuser(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="info@hb-china-cars.com",
                password="admin123",
                first_name="Admin",
                last_name="System",
            )
            self.stdout.write("  Superuser admin: created")
        else:
            self.stdout.write("  Superuser admin: exists")

    # ------------------------------------------------------------------
    def seed_system_config(self):
        from core.models import Currency
        from system_settings.models import SystemConfiguration

        if SystemConfiguration.objects.filter(pk=1).exists():
            self.stdout.write("  SystemConfiguration pk=1: exists")
            return

        da = Currency.objects.get(code="DA")
        admin = User.objects.get(username="admin")

        SystemConfiguration.objects.create(
            pk=1,
            # ── Company info ────────────────────────────────────────────
            company_name="HB China Cars",
            company_nif="123456789012345",
            company_address="Algérie",
            company_phone="+213 541 17 00 64",
            company_email="info@hb-china-cars.com",
            # ── Tax rates (Algeria 2025) ─────────────────────────────────
            # TVA 19% — standard rate for vehicle imports (9% is only for
            #           basic goods/tourism, does NOT apply to vehicles)
            default_tva_rate=19.00,
            # Customs tariff 30% — ceiling rate for standard petrol cars
            # imported from China (range 15–30% by displacement/category)
            default_tariff_rate=30.00,
            # Commission 4% — company default
            default_commission_rate=4.00,
            # ── Other defaults ───────────────────────────────────────────
            default_currency=da,
            reservation_duration_days=7,
            invoice_due_days=30,
            created_by=admin,
            updated_by=admin,
        )
        self.stdout.write("  SystemConfiguration pk=1: created")

    # ------------------------------------------------------------------
    def seed_tax_rates(self):
        from system_settings.models import TaxRateHistory

        admin = User.objects.get(username="admin")
        today = timezone.now().date()

        tax_defaults = [
            {
                "tax_type": "tva",
                "rate": 19.00,
                # 19% is the correct standard VAT rate for vehicle imports
                # in Algeria. The 9% reduced rate does NOT apply to vehicles.
                "description": "TVA standard Algérie — taux normal 19% (véhicules)",
            },
            {
                "tax_type": "tariff",
                "rate": 30.00,
                # 30% is the ceiling tariff for standard petrol passenger
                # vehicles imported from China (range 15–30% by category).
                # As of July 2025, duties are calculated on the Chinese
                # invoice price, not inflated Argus valuations.
                "description": "Droit de douane véhicules — taux plafond 30% (voitures particulières depuis Chine)",
            },
        ]

        for t in tax_defaults:
            obj, created = TaxRateHistory.objects.get_or_create(
                tax_type=t["tax_type"],
                effective_date=today,
                defaults={
                    "rate": t["rate"],
                    "description": t["description"],
                    "created_by": admin,
                    "updated_by": admin,
                },
            )
            self.stdout.write(
                f"  TaxRate {t['tax_type']} {t['rate']}%: {'created' if created else 'exists'}"
            )
