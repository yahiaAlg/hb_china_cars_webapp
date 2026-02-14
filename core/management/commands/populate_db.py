from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random
from faker import Faker

from core.models import UserProfile, Currency, ExchangeRate, SystemSetting
from system_settings.models import (
    SystemConfiguration,
    ExchangeRateHistory,
    TaxRateHistory,
    UserPreference,
)
from customers.models import Customer, CustomerNote
from suppliers.models import Supplier
from inventory.models import Vehicle, VehiclePhoto, StockAlert
from purchases.models import Purchase, FreightCost, CustomsDeclaration
from sales.models import Sale, Invoice
from payments.models import Payment, PaymentReminder, PaymentPlan, Installment
from commissions.models import (
    CommissionTier,
    CommissionPeriod,
    CommissionSummary,
    CommissionAdjustment,
    CommissionPayment,
)
from reports.models import ReportTemplate, ScheduledReport, ReportExecution

fake = Faker(["fr_FR"])


class Command(BaseCommand):
    help = "Populate the database with sample data for testing and development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before populating",
        )
        parser.add_argument(
            "--users",
            type=int,
            default=5,
            help="Number of users to create (default: 5)",
        )
        parser.add_argument(
            "--customers",
            type=int,
            default=10,
            help="Number of customers to create (default: 10)",
        )
        parser.add_argument(
            "--vehicles",
            type=int,
            default=15,
            help="Number of vehicles to create (default: 15)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting database population..."))

        if options["clear"]:
            self.clear_data()

        # Create data in order of dependencies
        self.create_users_and_profiles(options["users"])
        self.create_currencies()
        self.create_system_settings()
        self.create_suppliers()
        self.create_customers(options["customers"])
        self.create_purchases_and_inventory(options["vehicles"])
        self.create_sales_and_invoices()
        self.create_payments()
        self.create_commissions()
        self.create_reports()
        self.create_user_preferences()

        self.stdout.write(
            self.style.SUCCESS("Database population completed successfully!")
        )

    def clear_data(self):
        """Clear existing data from all models"""
        self.stdout.write("Clearing existing data...")

        # Delete in reverse order of dependencies
        ReportExecution.objects.all().delete()
        ScheduledReport.objects.all().delete()
        ReportTemplate.objects.all().delete()
        CommissionPayment.objects.all().delete()
        CommissionAdjustment.objects.all().delete()
        CommissionSummary.objects.all().delete()
        CommissionPeriod.objects.all().delete()
        CommissionTier.objects.all().delete()
        Installment.objects.all().delete()
        PaymentPlan.objects.all().delete()
        PaymentReminder.objects.all().delete()
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        Sale.objects.all().delete()
        VehiclePhoto.objects.all().delete()
        StockAlert.objects.all().delete()
        Vehicle.objects.all().delete()
        CustomsDeclaration.objects.all().delete()
        FreightCost.objects.all().delete()
        Purchase.objects.all().delete()
        CustomerNote.objects.all().delete()
        Customer.objects.all().delete()
        Supplier.objects.all().delete()
        UserPreference.objects.all().delete()
        TaxRateHistory.objects.all().delete()
        ExchangeRateHistory.objects.all().delete()
        SystemConfiguration.objects.all().delete()
        ExchangeRate.objects.all().delete()
        Currency.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        SystemSetting.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Existing data cleared."))

    def create_users_and_profiles(self, count):
        """Create users with different roles"""
        self.stdout.write("Creating users and profiles...")

        # Create superuser if doesn't exist
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@bureauauto.dz",
                password="admin123",
                first_name="Admin",
                last_name="System",
            )
            # Update the auto-created profile
            profile = admin.userprofile
            profile.role = "manager"
            profile.phone = "+213550000001"
            profile.default_commission_rate = 0
            profile.save()
            self.stdout.write(f"  Created superuser: admin")

        # Create manager
        if not User.objects.filter(username="manager").exists():
            manager = User.objects.create_user(
                username="manager",
                email="manager@bureauauto.dz",
                password="manager123",
                first_name="Ahmed",
                last_name="Manager",
            )
            profile = manager.userprofile
            profile.role = "manager"
            profile.phone = "+213550000002"
            profile.default_commission_rate = 15.00
            profile.save()
            self.stdout.write(f"  Created manager: Ahmed Manager")

        # Create traders
        trader_names = [
            ("Karim", "Benali"),
            ("Sofiane", "Haddad"),
            ("Yacine", "Boudraa"),
            ("Nadia", "Merabet"),
        ]

        for i, (first, last) in enumerate(trader_names[: count - 2], 1):
            username = f"trader{i}"
            if not User.objects.filter(username=username).exists():
                trader = User.objects.create_user(
                    username=username,
                    email=f"{username}@bureauauto.dz",
                    password="trader123",
                    first_name=first,
                    last_name=last,
                )
                profile = trader.userprofile
                profile.role = "trader"
                profile.phone = f"+2135500001{i:02d}"
                profile.default_commission_rate = 10.00 + random.randint(0, 5)
                profile.save()
                self.stdout.write(f"  Created trader: {first} {last}")

        # Create finance user
        if not User.objects.filter(username="finance").exists():
            finance = User.objects.create_user(
                username="finance",
                email="finance@bureauauto.dz",
                password="finance123",
                first_name="Fatima",
                last_name="Finance",
            )
            profile = finance.userprofile
            profile.role = "finance"
            profile.phone = "+213550000003"
            profile.default_commission_rate = 0
            profile.save()
            self.stdout.write(f"  Created finance user: Fatima Finance")

        # Create auditor
        if not User.objects.filter(username="auditor").exists():
            auditor = User.objects.create_user(
                username="auditor",
                email="auditor@bureauauto.dz",
                password="auditor123",
                first_name="Samir",
                last_name="Auditor",
            )
            profile = auditor.userprofile
            profile.role = "auditor"
            profile.phone = "+213550000004"
            profile.default_commission_rate = 0
            profile.save()
            self.stdout.write(f"  Created auditor: Samir Auditor")

    def create_currencies(self):
        """Create currencies and exchange rates"""
        self.stdout.write("Creating currencies...")

        currencies_data = [
            ("DA", "Dinar Algérien", "د.ج"),
            ("USD", "Dollar Américain", "$"),
            ("CNY", "Yuan Chinois", "¥"),
            ("EUR", "Euro", "€"),
        ]

        self.currencies = {}
        for code, name, symbol in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=code, defaults={"name": name, "symbol": symbol, "is_active": True}
            )
            self.currencies[code] = currency
            if created:
                self.stdout.write(f"  Created currency: {code} - {name}")

        # Create exchange rates
        self.stdout.write("Creating exchange rates...")
        rates = [
            ("USD", "DA", 135.50),
            ("CNY", "DA", 18.75),
            ("EUR", "DA", 145.20),
        ]

        for from_code, to_code, rate in rates:
            ExchangeRate.objects.get_or_create(
                from_currency=self.currencies[from_code],
                to_currency=self.currencies[to_code],
                effective_date=timezone.now().date(),
                defaults={
                    "rate": rate,
                    "created_by": User.objects.get(username="admin"),
                    "notes": f"Official rate for {from_code} to {to_code}",
                },
            )
            self.stdout.write(f"  Created rate: 1 {from_code} = {rate} {to_code}")

    def create_system_settings(self):
        """Create system configuration and settings"""
        self.stdout.write("Creating system settings...")

        # System Configuration
        config, created = SystemConfiguration.objects.get_or_create(
            pk=1,
            defaults={
                "company_name": "Bureau de Commerce Automobile Algérien",
                "company_nif": "123456789012345",
                "company_address": "123 Boulevard Mohamed VI, Alger Centre, Alger, Algérie",
                "company_phone": "+213 21 123 456",
                "company_email": "contact@bureauauto.dz",
                "default_tva_rate": 19.00,
                "default_tariff_rate": 25.00,
                "default_commission_rate": 10.00,
                "default_currency": self.currencies["DA"],
                "reservation_duration_days": 7,
                "invoice_due_days": 30,
                "enable_email_notifications": True,
                "enable_overdue_alerts": True,
                "overdue_alert_days": 7,
                "created_by": User.objects.get(username="admin"),
            },
        )
        if created:
            self.stdout.write("  Created system configuration")

        # Tax Rate History
        tax_rates = [
            ("tva", 19.00, "TVA standard"),
            ("tariff", 25.00, "Tarif douanier standard"),
            ("tva", 9.00, "TVA réduite"),
        ]

        for tax_type, rate, desc in tax_rates:
            TaxRateHistory.objects.get_or_create(
                tax_type=tax_type,
                rate=rate,
                effective_date=timezone.now().date()
                - timedelta(days=random.randint(0, 365)),
                defaults={
                    "description": desc,
                    "created_by": User.objects.get(username="admin"),
                },
            )
        self.stdout.write(f"  Created {len(tax_rates)} tax rate records")

        # Exchange Rate History
        for _ in range(5):
            ExchangeRateHistory.objects.create(
                from_currency=self.currencies["USD"],
                to_currency=self.currencies["DA"],
                rate=Decimal("135.50") + Decimal(str(random.uniform(-5, 5))),
                effective_date=timezone.now().date()
                - timedelta(days=random.randint(1, 90)),
                source="Banque d'Algérie",
                notes="Historical exchange rate",
                created_by=User.objects.get(username="admin"),
            )
        self.stdout.write("  Created exchange rate history")

    def create_suppliers(self):
        """Create Chinese car suppliers"""
        self.stdout.write("Creating suppliers...")

        suppliers_data = [
            {
                "name": "Shanghai Auto Export Co.",
                "contact_person": "Li Wei",
                "phone": "+86 138 1234 5678",
                "email": "liwei@shanghaiauto.cn",
                "address": "1234 Auto Export Road, Shanghai, China",
                "currency": self.currencies["USD"],
                "payment_terms": "30% advance, 70% against B/L",
            },
            {
                "name": "Guangzhou Vehicle Trading Ltd",
                "contact_person": "Zhang Ming",
                "phone": "+86 139 8765 4321",
                "email": "zhangming@gzhvehicle.com",
                "address": "567 Trading Plaza, Guangzhou, China",
                "currency": self.currencies["CNY"],
                "payment_terms": "LC at sight",
            },
            {
                "name": "Beijing International Motors",
                "contact_person": "Wang Fang",
                "phone": "+86 135 2468 1357",
                "email": "wangfang@bjmotors.cn",
                "address": "789 Motor Street, Beijing, China",
                "currency": self.currencies["USD"],
                "payment_terms": "50% advance, 50% on delivery",
            },
            {
                "name": "Shenzhen Premium Cars Export",
                "contact_person": "Chen Hua",
                "phone": "+86 136 9876 5432",
                "email": "chenhua@szpremiumcars.com",
                "address": "321 Export Zone, Shenzhen, China",
                "currency": self.currencies["USD"],
                "payment_terms": "T/T in advance",
            },
        ]

        self.suppliers = []
        for data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=data["name"],
                defaults={
                    "contact_person": data["contact_person"],
                    "phone": data["phone"],
                    "email": data["email"],
                    "address": data["address"],
                    "currency": data["currency"],
                    "payment_terms": data["payment_terms"],
                    "is_active": True,
                    "created_by": User.objects.get(username="admin"),
                },
            )
            self.suppliers.append(supplier)
            if created:
                self.stdout.write(f"  Created supplier: {supplier.name}")

    def create_customers(self, count):
        """Create Algerian customers"""
        self.stdout.write("Creating customers...")

        wilayas = [
            ("16", "Alger"),
            ("31", "Oran"),
            ("25", "Constantine"),
            ("09", "Blida"),
            ("23", "Annaba"),
            ("13", "Tlemcen"),
            ("19", "Sétif"),
            ("05", "Batna"),
            ("22", "Sidi Bel Abbès"),
            ("10", "Bouira"),
            ("34", "Bordj Bou Arréridj"),
            ("35", "Boumerdès"),
        ]

        self.customers = []
        for i in range(count):
            is_company = random.choice([True, False])

            if is_company:
                name = fake.company()
                customer_type = "company"
                nif = f"{random.randint(100000000, 999999999)}"
            else:
                name = f"{fake.first_name()} {fake.last_name()}"
                customer_type = "individual"
                nif = ""

            wilaya_code, wilaya_name = random.choice(wilayas)

            customer, created = Customer.objects.get_or_create(
                name=name,
                defaults={
                    "customer_type": customer_type,
                    "nif_tax_id": nif,
                    "phone": f"0{random.randint(500000000, 599999999)}",
                    "email": fake.email() if random.choice([True, False]) else "",
                    "address": fake.address(),
                    "wilaya": wilaya_code,
                    "notes": (
                        fake.text(max_nb_chars=100)
                        if random.choice([True, False])
                        else ""
                    ),
                    "is_active": True,
                    "created_by": User.objects.get(username="admin"),
                },
            )

            self.customers.append(customer)
            if created:
                self.stdout.write(f"  Created customer: {name} ({customer_type})")

                # Add customer notes
                if random.choice([True, False]):
                    CustomerNote.objects.create(
                        customer=customer,
                        note=fake.text(max_nb_chars=200),
                        is_important=random.choice([True, False]),
                        created_by=User.objects.get(username="admin"),
                    )

    def create_purchases_and_inventory(self, count):
        """Create purchases and vehicle inventory"""
        self.stdout.write("Creating purchases and vehicles...")

        car_models = [
            ("Toyota", "Corolla", 2023, "Blanc"),
            ("Hyundai", "Tucson", 2023, "Gris"),
            ("Kia", "Sportage", 2022, "Noir"),
            ("Volkswagen", "Golf", 2023, "Rouge"),
            ("Renault", "Duster", 2022, "Bleu"),
            ("Peugeot", "3008", 2023, "Gris"),
            ("Mercedes", "C-Class", 2023, "Argent"),
            ("BMW", "X5", 2022, "Noir"),
            ("Audi", "A4", 2023, "Blanc"),
            ("Nissan", "Qashqai", 2022, "Rouge"),
        ]

        self.vehicles = []
        self.purchases = []

        for i in range(count):
            # Create purchase
            supplier = random.choice(self.suppliers)
            purchase_date = timezone.now().date() - timedelta(
                days=random.randint(30, 180)
            )

            # FOB price in supplier's currency
            fob_price = Decimal(str(random.uniform(8000, 35000))).quantize(
                Decimal("0.01")
            )

            # Exchange rate
            if supplier.currency.code == "USD":
                exchange_rate = Decimal("135.50")
            elif supplier.currency.code == "CNY":
                exchange_rate = Decimal("18.75")
            else:
                exchange_rate = Decimal("1.00")

            purchase = Purchase.objects.create(
                purchase_date=purchase_date,
                supplier=supplier,
                purchase_price_fob=fob_price,
                currency=supplier.currency,
                exchange_rate_to_da=exchange_rate,
                notes=(
                    fake.text(max_nb_chars=100) if random.choice([True, False]) else ""
                ),
                created_by=User.objects.get(username="admin"),
            )
            self.purchases.append(purchase)

            # Create freight cost
            freight_cost_usd = Decimal(str(random.uniform(800, 2500))).quantize(
                Decimal("0.01")
            )
            FreightCost.objects.create(
                purchase=purchase,
                freight_method=random.choice(["sea", "air"]),
                freight_cost=freight_cost_usd,
                freight_currency=self.currencies["USD"],
                freight_exchange_rate=Decimal("135.50"),
                insurance_cost_da=Decimal(str(random.uniform(50000, 150000))).quantize(
                    Decimal("0.01")
                ),
                other_logistics_costs_da=Decimal(
                    str(random.uniform(20000, 80000))
                ).quantize(Decimal("0.01")),
                created_by=User.objects.get(username="admin"),
            )

            # Create customs declaration
            cif_value = purchase.purchase_price_da + (
                freight_cost_usd * Decimal("135.50")
            )
            tariff_rate = Decimal("25.00")
            import_duty = cif_value * (tariff_rate / Decimal("100"))
            tva_rate = Decimal("19.00")
            tva_amount = (cif_value + import_duty) * (tva_rate / Decimal("100"))

            CustomsDeclaration.objects.create(
                purchase=purchase,
                declaration_date=purchase_date + timedelta(days=random.randint(15, 45)),
                declaration_number=f"DOU-{random.randint(100000, 999999)}",
                cif_value_da=cif_value,
                customs_tariff_rate=tariff_rate,
                import_duty_da=import_duty,
                tva_rate=tva_rate,
                tva_amount_da=tva_amount,
                other_fees_da=Decimal(str(random.uniform(50000, 200000))).quantize(
                    Decimal("0.01")
                ),
                is_cleared=random.choice([True, True, True, False]),  # 75% cleared
                clearance_date=(
                    purchase_date + timedelta(days=random.randint(30, 60))
                    if random.choice([True, True, True, False])
                    else None
                ),
                notes="",
                created_by=User.objects.get(username="admin"),
            )

            # Create vehicle
            make, model, year, color = random.choice(car_models)
            status = random.choice(
                ["in_transit", "at_customs", "available", "available", "available"]
            )

            # If customs cleared, vehicle is available
            if purchase.customs_declaration.is_cleared:
                status = random.choice(["available", "available", "reserved"])

            vehicle = Vehicle.objects.create(
                vin_chassis=f"VIN{random.randint(1000000000, 9999999999)}",
                make=make,
                model=model,
                year=year,
                color=color,
                engine_type=f'{random.choice([1.5, 1.6, 2.0, 2.5])}L {random.choice(["Essence", "Diesel", "Hybride"])}',
                specifications=fake.text(max_nb_chars=150),
                vehicle_purchase=purchase,
                status=status,
                created_by=User.objects.get(username="admin"),
            )
            self.vehicles.append(vehicle)
            self.stdout.write(f"  Created vehicle: {vehicle}")

    def create_sales_and_invoices(self):
        """Create sales and invoices for available vehicles"""
        self.stdout.write("Creating sales and invoices...")

        available_vehicles = [
            v for v in self.vehicles if v.status in ["available", "reserved"]
        ]
        traders = list(User.objects.filter(userprofile__role="trader"))

        self.sales = []
        self.invoices = []

        # Create sales for about 60% of available vehicles
        for vehicle in available_vehicles[: int(len(available_vehicles) * 0.6)]:
            customer = random.choice(self.customers)
            trader = random.choice(traders)

            # Calculate sale price with margin
            landed_cost = vehicle.landed_cost
            margin_percent = random.uniform(15, 35)
            sale_price = landed_cost * Decimal(str(1 + margin_percent / 100))

            sale_date = timezone.now().date() - timedelta(days=random.randint(1, 30))

            sale = Sale.objects.create(
                sale_number=f'VEN-{sale_date.strftime("%Y%m%d")}-{random.randint(1, 999):03d}',
                sale_date=sale_date,
                vehicle=vehicle,
                customer=customer,
                assigned_trader=trader,
                sale_price=sale_price.quantize(Decimal("0.01")),
                payment_method=random.choice(
                    ["cash", "bank_transfer", "installment", "check"]
                ),
                down_payment=(
                    (sale_price * Decimal("0.3")).quantize(Decimal("0.01"))
                    if random.choice([True, False])
                    else Decimal("0")
                ),
                commission_rate=trader.userprofile.default_commission_rate,
                is_finalized=True,
                notes="",
                created_by=trader,
            )
            self.sales.append(sale)

            # Create invoice
            invoice = Invoice.objects.create(
                invoice_number=f'FAC-{sale_date.strftime("%Y%m%d")}-{random.randint(1, 999):03d}',
                invoice_date=sale_date,
                due_date=sale_date + timedelta(days=30),
                sale=sale,
                customer=customer,
                subtotal_ht=(sale_price / Decimal("1.19")).quantize(Decimal("0.01")),
                tva_rate=Decimal("19.00"),
                tva_amount=(sale_price - (sale_price / Decimal("1.19"))).quantize(
                    Decimal("0.01")
                ),
                total_ttc=sale_price.quantize(Decimal("0.01")),
                amount_paid=sale.down_payment,
                balance_due=sale_price - sale.down_payment,
                status="issued" if sale.down_payment < sale_price else "paid",
                notes="",
                created_by=trader,
            )
            self.invoices.append(invoice)
            self.stdout.write(f"  Created sale: {sale.sale_number} - {customer.name}")

    def create_payments(self):
        """Create payments for invoices"""
        self.stdout.write("Creating payments...")

        for invoice in self.invoices:
            if invoice.status == "paid":
                # Full payment
                Payment.objects.create(
                    payment_number=f'PAY-{timezone.now().strftime("%Y%m%d")}-{random.randint(1, 999):03d}',
                    payment_date=invoice.invoice_date
                    + timedelta(days=random.randint(0, 15)),
                    invoice=invoice,
                    amount=invoice.total_ttc,
                    payment_method=random.choice(["cash", "bank_transfer", "check"]),
                    bank_reference=(
                        f"REF-{random.randint(100000, 999999)}"
                        if random.choice([True, False])
                        else ""
                    ),
                    is_confirmed=True,
                    created_by=User.objects.get(username="finance"),
                )
            elif invoice.amount_paid > 0:
                # Partial payment (down payment recorded)
                Payment.objects.create(
                    payment_number=f'PAY-{timezone.now().strftime("%Y%m%d")}-{random.randint(1, 999):03d}',
                    payment_date=invoice.sale.sale_date,
                    invoice=invoice,
                    amount=invoice.amount_paid,
                    payment_method=invoice.sale.payment_method,
                    is_confirmed=True,
                    created_by=User.objects.get(username="finance"),
                )

                # Create payment reminder for overdue invoices
                if invoice.is_overdue and random.choice([True, False]):
                    PaymentReminder.objects.create(
                        invoice=invoice,
                        reminder_date=timezone.now().date()
                        - timedelta(days=random.randint(1, 7)),
                        reminder_type=random.choice(["email", "phone", "sms"]),
                        message=fake.text(max_nb_chars=200),
                        sent_by=User.objects.get(username="finance"),
                        created_by=User.objects.get(username="finance"),
                    )

            # Create payment plan for some installment sales
            if invoice.sale.payment_method == "installment" and invoice.balance_due > 0:
                plan = PaymentPlan.objects.create(
                    invoice=invoice,
                    total_amount=invoice.balance_due,
                    down_payment=Decimal("0"),
                    number_of_installments=random.choice([6, 12, 24]),
                    start_date=invoice.invoice_date + timedelta(days=30),
                    status="active",
                    notes="",
                    created_by=User.objects.get(username="finance"),
                )
                self.stdout.write(
                    f"    Created payment plan for: {invoice.invoice_number}"
                )

    def create_commissions(self):
        """Create commission tiers, periods, and summaries"""
        self.stdout.write("Creating commissions...")

        # Create commission tiers
        tiers_data = [
            ("Bronze", 0, 5, 10.00),
            ("Silver", 6, 10, 12.00),
            ("Gold", 11, 20, 15.00),
            ("Platinum", 21, None, 20.00),
        ]

        for name, min_sales, max_sales, rate in tiers_data:
            CommissionTier.objects.get_or_create(
                name=name,
                defaults={
                    "min_sales_count": min_sales,
                    "max_sales_count": max_sales,
                    "commission_rate": rate,
                    "is_active": True,
                    "created_by": User.objects.get(username="admin"),
                },
            )
            self.stdout.write(f"  Created commission tier: {name}")

        # Create commission periods for last 3 months
        today = timezone.now().date()
        traders = list(User.objects.filter(userprofile__role="trader"))

        for i in range(3):
            month_date = today.replace(day=1) - timedelta(days=i * 30)

            period, created = CommissionPeriod.objects.get_or_create(
                year=month_date.year,
                month=month_date.month,
                defaults={
                    "is_closed": i > 0,  # Close past months
                    "closed_date": (
                        timezone.now() - timedelta(days=30) if i > 0 else None
                    ),
                    "closed_by": User.objects.get(username="admin") if i > 0 else None,
                },
            )

            if created:
                self.stdout.write(f"  Created commission period: {period}")

            # Create commission summaries for each trader
            for trader in traders:
                # Get sales for this period
                sales = Sale.objects.filter(
                    assigned_trader=trader,
                    sale_date__year=month_date.year,
                    sale_date__month=month_date.month,
                    is_finalized=True,
                )

                if sales.exists():
                    total_sales = sum(s.sale_price for s in sales)
                    total_margin = sum(s.margin_amount for s in sales)
                    total_commission = sum(s.commission_amount for s in sales)

                    CommissionSummary.objects.create(
                        trader=trader,
                        period=period,
                        sales_count=sales.count(),
                        total_sales_value=total_sales,
                        total_margin=total_margin,
                        base_commission=total_commission,
                        tier_bonus=Decimal("0"),
                        total_commission=total_commission,
                        payout_status="pending" if not period.is_closed else "approved",
                        created_by=User.objects.get(username="admin"),
                    )
                    self.stdout.write(
                        f"    Commission summary for {trader.username} - {period}"
                    )

    def create_reports(self):
        """Create report templates and scheduled reports"""
        self.stdout.write("Creating reports...")

        # Create report templates
        templates_data = [
            ("Analyse de Profit Mensuelle", "profit_analysis", True),
            ("Performance des Traders", "trader_performance", True),
            ("État du Stock", "inventory_status", True),
            ("Résumé des Ventes", "sales_summary", True),
            ("État des Paiements", "payment_status", False),
        ]

        for name, report_type, is_public in templates_data:
            template, created = ReportTemplate.objects.get_or_create(
                name=name,
                defaults={
                    "report_type": report_type,
                    "description": fake.text(max_nb_chars=100),
                    "filter_parameters": {"date_range": "last_month"},
                    "is_public": is_public,
                    "allowed_roles": ["manager", "finance"] if not is_public else [],
                    "created_by": User.objects.get(username="admin"),
                },
            )
            if created:
                self.stdout.write(f"  Created report template: {name}")

        # Create scheduled reports
        templates = list(ReportTemplate.objects.all())
        managers = list(User.objects.filter(userprofile__role="manager"))

        for template in templates[:2]:
            scheduled = ScheduledReport.objects.create(
                template=template,
                name=f"Planification - {template.name}",
                frequency=random.choice(["daily", "weekly", "monthly"]),
                email_subject=f"Rapport automatique: {template.name}",
                next_run=timezone.now() + timedelta(days=1),
                status="active",
                created_by=User.objects.get(username="admin"),
            )
            scheduled.recipients.set(managers)
            self.stdout.write(f"  Created scheduled report: {scheduled.name}")

        # Create report executions
        for template in templates[:3]:
            ReportExecution.objects.create(
                template=template,
                executed_by=User.objects.get(username="admin"),
                start_time=timezone.now() - timedelta(days=random.randint(1, 30)),
                end_time=timezone.now()
                - timedelta(days=random.randint(1, 30))
                + timedelta(minutes=5),
                status="completed",
                record_count=random.randint(50, 500),
                created_by=User.objects.get(username="admin"),
            )
            self.stdout.write(f"  Created report execution for: {template.name}")

    def create_user_preferences(self):
        """Create user preferences"""
        self.stdout.write("Creating user preferences...")

        users = User.objects.filter(is_superuser=False)

        for user in users:
            UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    "theme": random.choice(["light", "dark", "auto"]),
                    "language": random.choice(["fr", "ar", "en"]),
                    "dashboard_widgets": [
                        "sales_chart",
                        "inventory_status",
                        "pending_payments",
                    ],
                    "default_page_size": random.choice([10, 20, 50]),
                    "email_notifications": True,
                    "browser_notifications": random.choice([True, False]),
                    "default_export_format": random.choice(["excel", "csv", "pdf"]),
                    "created_by": user,
                },
            )
            self.stdout.write(f"  Created preferences for: {user.username}")
