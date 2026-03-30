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
from purchases.models import (
    Purchase,
    PurchaseLineItem,
    FreightCost,
    CustomsDeclaration,
    LineItemFreightCost,
    LineItemCustomsDeclaration,
)
from sales.models import Sale, SaleLineItem, Invoice
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
        SaleLineItem.objects.all().delete()
        Sale.objects.all().delete()
        VehiclePhoto.objects.all().delete()
        StockAlert.objects.all().delete()
        Vehicle.objects.all().delete()
        LineItemCustomsDeclaration.objects.all().delete()
        LineItemFreightCost.objects.all().delete()
        CustomsDeclaration.objects.all().delete()
        FreightCost.objects.all().delete()
        PurchaseLineItem.objects.all().delete()
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

        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@bureauauto.dz",
                password="admin123",
                first_name="Admin",
                last_name="System",
            )
            profile = admin.userprofile
            profile.role = "manager"
            profile.phone = "+213550000001"
            profile.default_commission_rate = 0
            profile.save()
            self.stdout.write("  Created superuser: admin")

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
            self.stdout.write("  Created manager: Ahmed Manager")

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
            self.stdout.write("  Created finance user: Fatima Finance")

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
            self.stdout.write("  Created auditor: Samir Auditor")

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

        history_rates = [
            ("USD", "DA", Decimal("130.25"), 90),
            ("USD", "DA", Decimal("132.00"), 60),
            ("USD", "DA", Decimal("133.75"), 30),
            ("USD", "DA", Decimal("134.50"), 14),
            ("USD", "DA", Decimal("135.50"), 1),
            ("CNY", "DA", Decimal("18.10"), 90),
            ("CNY", "DA", Decimal("18.45"), 30),
            ("CNY", "DA", Decimal("18.75"), 1),
        ]
        for from_code, to_code, rate, days_ago in history_rates:
            ExchangeRateHistory.objects.get_or_create(
                from_currency=self.currencies[from_code],
                to_currency=self.currencies[to_code],
                effective_date=timezone.now().date() - timedelta(days=days_ago),
                defaults={
                    "rate": rate,
                    "source": "Banque d'Algérie",
                    "notes": "Historical exchange rate",
                    "created_by": User.objects.get(username="admin"),
                },
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
                    "country": "Chine",
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

        customer_data = [
            {
                "name": "Mohamed Boudiaf",
                "customer_type": "individual",
                "phone": "+213550111001",
                "address": "15 Rue des Martyrs, Alger",
                "wilaya": "16",
            },
            {
                "name": "Entreprise SARL AutoTrans",
                "customer_type": "company",
                "nif_tax_id": "001234567890123",
                "phone": "+213550111002",
                "address": "Zone Industrielle, Annaba",
                "wilaya": "23",
            },
            {
                "name": "Rachid Amrani",
                "customer_type": "individual",
                "phone": "+213550111003",
                "address": "45 Boulevard Krim Belkacem, Oran",
                "wilaya": "31",
            },
            {
                "name": "Fatima Zohra Khelil",
                "customer_type": "individual",
                "phone": "+213550111004",
                "address": "12 Rue Didouche Mourad, Constantine",
                "wilaya": "25",
            },
            {
                "name": "SPA Groupe Logistique National",
                "customer_type": "company",
                "nif_tax_id": "009876543210987",
                "phone": "+213550111005",
                "address": "Lotissement Commercial, Sétif",
                "wilaya": "19",
            },
            {
                "name": "Kamel Ouahrani",
                "customer_type": "individual",
                "phone": "+213550111006",
                "address": "67 Avenue Ben M'hidi, Tizi Ouzou",
                "wilaya": "15",
            },
            {
                "name": "Amir Touati",
                "customer_type": "individual",
                "phone": "+213550111007",
                "address": "23 Rue de l'Indépendance, Batna",
                "wilaya": "05",
            },
            {
                "name": "Samira Benhaddou",
                "customer_type": "individual",
                "phone": "+213550111008",
                "address": "89 Boulevard du 1er Novembre, Blida",
                "wilaya": "09",
            },
            {
                "name": "EURL Transport et Services",
                "customer_type": "company",
                "nif_tax_id": "005678901234567",
                "phone": "+213550111009",
                "address": "Rue Larbi Ben M'hidi, Mostaganem",
                "wilaya": "27",
            },
            {
                "name": "Hamza Laribi",
                "customer_type": "individual",
                "phone": "+213550111010",
                "address": "14 Rue Ahmed Bey, Skikda",
                "wilaya": "21",
            },
        ]

        self.customers = []
        for i, data in enumerate(customer_data[:count]):
            customer, created = Customer.objects.get_or_create(
                phone=data["phone"],
                defaults={
                    "name": data["name"],
                    "customer_type": data["customer_type"],
                    "nif_tax_id": data.get("nif_tax_id", ""),
                    "address": data["address"],
                    "wilaya": data["wilaya"],
                    "is_active": True,
                    "created_by": User.objects.get(username="admin"),
                },
            )
            self.customers.append(customer)
            if created:
                self.stdout.write(f"  Created customer: {customer.name}")

                # Add a customer note
                CustomerNote.objects.create(
                    customer=customer,
                    note=fake.text(max_nb_chars=100),
                    is_important=random.choice([True, False]),
                    created_by=User.objects.get(username="admin"),
                )

    def create_purchases_and_inventory(self, vehicle_count):
        """Create purchases, freight, customs, and vehicles"""
        self.stdout.write("Creating purchases and inventory...")

        car_models = [
            ("Chery", "Tiggo 8 Pro", "SUV"),
            ("BYD", "Han EV", "Berline"),
            ("Haval", "H6", "SUV"),
            ("MG", "ZS", "SUV"),
            ("Geely", "Coolray", "SUV"),
            ("SAIC", "MG5", "Berline"),
            ("Changan", "CS75 Plus", "SUV"),
            ("GAC", "Trumpchi GS4", "SUV"),
            ("JAC", "T8 Pro", "Pick-up"),
            ("Dongfeng", "AX7", "SUV"),
        ]

        colors = [
            "Blanc Perle",
            "Noir Minuit",
            "Gris Métallisé",
            "Bleu Azur",
            "Rouge Cardinal",
            "Argent",
        ]

        self.vehicles = []
        admin_user = User.objects.get(username="admin")

        for idx in range(vehicle_count):
            supplier = random.choice(self.suppliers)
            exchange_rate = (
                Decimal("135.50")
                if supplier.currency.code == "USD"
                else Decimal("18.75")
            )
            purchase_date = timezone.now().date() - timedelta(
                days=random.randint(30, 180)
            )

            purchase = Purchase.objects.create(
                purchase_date=purchase_date,
                supplier=supplier,
                currency=supplier.currency,
                exchange_rate_to_da=exchange_rate,
                cost_mode="container",
                notes="",
                created_by=admin_user,
            )

            make, model_name, _ = random.choice(car_models)
            year = random.choice([2022, 2023, 2024])
            fob_price = Decimal(str(random.uniform(12000, 35000))).quantize(
                Decimal("0.01")
            )

            line_item = PurchaseLineItem.objects.create(
                purchase=purchase,
                line_number=1,
                make=make,
                model=model_name,
                year=year,
                color=random.choice(colors),
                engine_type=random.choice(
                    ["1.5T", "2.0T", "1.6L", "Electric", "Hybrid"]
                ),
                vin_chassis=f"VIN{random.randint(1000000000, 9999999999)}",
                fob_price=fob_price,
                notes="",
                created_by=admin_user,
            )

            # Freight
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
                created_by=admin_user,
            )

            # Customs
            cif_value = purchase.total_fob_da + (freight_cost_usd * Decimal("135.50"))
            tariff_rate = Decimal("25.00")
            import_duty = cif_value * (tariff_rate / Decimal("100"))
            tva_rate = Decimal("19.00")
            tva_amount = (cif_value + import_duty) * (tva_rate / Decimal("100"))

            is_cleared = random.choice([True, True, True, False])
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
                is_cleared=is_cleared,
                clearance_date=(
                    purchase_date + timedelta(days=random.randint(30, 60))
                    if is_cleared
                    else None
                ),
                notes="",
                created_by=admin_user,
            )

            # Vehicle status
            if is_cleared:
                status = random.choice(["available", "available", "reserved"])
            else:
                status = random.choice(["in_transit", "at_customs", "available"])

            vehicle = Vehicle.objects.create(
                purchase_line_item=line_item,
                vin_chassis=line_item.vin_chassis,
                make=line_item.make,
                model=line_item.model,
                year=line_item.year,
                color=line_item.color,
                engine_type=line_item.engine_type,
                specifications=fake.text(max_nb_chars=150),
                status=status,
                created_by=admin_user,
            )
            self.vehicles.append(vehicle)
            self.stdout.write(f"  Created vehicle: {vehicle}")

    def create_sales_and_invoices(self):
        """Create sales with one or more vehicles per sale (SaleLineItems)."""
        self.stdout.write("Creating sales and invoices...")

        available_vehicles = [
            v for v in self.vehicles if v.status in ["available", "reserved"]
        ]
        traders = list(User.objects.filter(userprofile__role="trader"))
        admin_user = User.objects.get(username="admin")

        self.sales = []
        self.invoices = []

        # Shuffle vehicles so multi-vehicle sales get random combos
        random.shuffle(available_vehicles)

        vehicle_pool = list(available_vehicles)
        # Sell roughly 60 % of available vehicles
        target_count = int(len(vehicle_pool) * 0.6)
        sold_count = 0

        while sold_count < target_count and vehicle_pool:
            # Randomly decide: single-vehicle (80 %) or multi-vehicle sale (20 %)
            if len(vehicle_pool) >= 2 and random.random() < 0.20:
                vehicles_in_sale = vehicle_pool[:2]
                vehicle_pool = vehicle_pool[2:]
            else:
                vehicles_in_sale = vehicle_pool[:1]
                vehicle_pool = vehicle_pool[1:]

            customer = random.choice(self.customers)
            trader = random.choice(traders)
            sale_date = timezone.now().date() - timedelta(days=random.randint(1, 90))

            sale = Sale.objects.create(
                sale_number=f'VTE-{sale_date.strftime("%Y%m%d")}-{random.randint(1, 999):03d}',
                sale_date=sale_date,
                customer=customer,
                assigned_trader=trader,
                payment_method=random.choice(
                    ["cash", "bank_transfer", "installment", "check"]
                ),
                down_payment=Decimal("0"),  # set after line items
                commission_rate=trader.userprofile.default_commission_rate,
                is_finalized=True,
                notes="",
                created_by=trader,
            )

            total_sale_price = Decimal("0")
            for line_num, vehicle in enumerate(vehicles_in_sale, 1):
                landed_cost = vehicle.landed_cost
                margin_percent = random.uniform(15, 35)
                line_price = (
                    landed_cost * Decimal(str(1 + margin_percent / 100))
                ).quantize(Decimal("0.01"))
                total_sale_price += line_price

                SaleLineItem.objects.create(
                    sale=sale,
                    vehicle=vehicle,
                    sale_price=line_price,
                    line_number=line_num,
                    notes="",
                    created_by=trader,
                )

            # Optional down payment (30 % chance, 30 % of total)
            down_payment = Decimal("0")
            if random.choice([True, False, False]):
                down_payment = (total_sale_price * Decimal("0.3")).quantize(
                    Decimal("0.01")
                )

            Sale.objects.filter(pk=sale.pk).update(down_payment=down_payment)
            sale.refresh_from_db()
            sale.recalculate_commission()

            self.sales.append(sale)
            sold_count += len(vehicles_in_sale)

            # Invoice
            invoice = Invoice.objects.create(
                invoice_number=f'FAC-{sale_date.strftime("%Y%m%d")}-{random.randint(1, 999):03d}',
                invoice_date=sale_date,
                due_date=sale_date + timedelta(days=30),
                sale=sale,
                customer=customer,
                subtotal_ht=(total_sale_price / Decimal("1.19")).quantize(
                    Decimal("0.01")
                ),
                tva_rate=Decimal("19.00"),
                tva_amount=(
                    total_sale_price - (total_sale_price / Decimal("1.19"))
                ).quantize(Decimal("0.01")),
                total_ttc=total_sale_price.quantize(Decimal("0.01")),
                amount_paid=down_payment,
                balance_due=(total_sale_price - down_payment).quantize(Decimal("0.01")),
                status="issued" if down_payment < total_sale_price else "paid",
                notes="",
                created_by=trader,
            )
            self.invoices.append(invoice)

            vehicle_labels = ", ".join(f"{v.make} {v.model}" for v in vehicles_in_sale)
            self.stdout.write(
                f"  Created sale: {sale.sale_number} — {customer.name} "
                f"({len(vehicles_in_sale)} véhicule(s): {vehicle_labels})"
            )

    def create_payments(self):
        """Create payments for invoices"""
        self.stdout.write("Creating payments...")

        finance_user = User.objects.get(username="finance")

        for invoice in self.invoices:
            if invoice.status == "paid":
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
                    created_by=finance_user,
                )
            elif invoice.amount_paid > 0:
                # Down payment
                Payment.objects.create(
                    payment_number=f'PAY-{timezone.now().strftime("%Y%m%d")}-{random.randint(1, 999):03d}',
                    payment_date=invoice.sale.sale_date,
                    invoice=invoice,
                    amount=invoice.amount_paid,
                    payment_method=invoice.sale.payment_method,
                    is_confirmed=True,
                    created_by=finance_user,
                )

                # Reminder for overdue invoices
                if invoice.is_overdue and random.choice([True, False]):
                    PaymentReminder.objects.create(
                        invoice=invoice,
                        reminder_date=timezone.now().date()
                        - timedelta(days=random.randint(1, 7)),
                        reminder_type=random.choice(["email", "phone", "sms"]),
                        message=fake.text(max_nb_chars=200),
                        sent_by=finance_user,
                        created_by=finance_user,
                    )

            # Payment plan for installment sales with outstanding balance
            if invoice.sale.payment_method == "installment" and invoice.balance_due > 0:
                PaymentPlan.objects.create(
                    invoice=invoice,
                    total_amount=invoice.balance_due,
                    down_payment=Decimal("0"),
                    number_of_installments=random.choice([6, 12, 24]),
                    start_date=invoice.invoice_date + timedelta(days=30),
                    status="active",
                    notes="",
                    created_by=finance_user,
                )
                self.stdout.write(
                    f"    Created payment plan for: {invoice.invoice_number}"
                )

    def create_commissions(self):
        """Create commission tiers, periods, and summaries"""
        self.stdout.write("Creating commissions...")

        tiers_data = [
            ("Bronze", 0, 5, 10.00),
            ("Silver", 6, 10, 12.00),
            ("Gold", 11, 20, 15.00),
            ("Platinum", 21, None, 20.00),
        ]

        admin_user = User.objects.get(username="admin")

        for name, min_sales, max_sales, rate in tiers_data:
            CommissionTier.objects.get_or_create(
                name=name,
                defaults={
                    "min_sales_count": min_sales,
                    "max_sales_count": max_sales,
                    "commission_rate": rate,
                    "is_active": True,
                    "created_by": admin_user,
                },
            )
            self.stdout.write(f"  Created commission tier: {name}")

        today = timezone.now().date()
        traders = list(User.objects.filter(userprofile__role="trader"))

        for i in range(3):
            month_date = today.replace(day=1) - timedelta(days=i * 30)

            period, created = CommissionPeriod.objects.get_or_create(
                year=month_date.year,
                month=month_date.month,
                defaults={
                    "is_closed": i > 0,
                    "closed_date": (
                        timezone.now() - timedelta(days=30) if i > 0 else None
                    ),
                    "closed_by": admin_user if i > 0 else None,
                },
            )

            if created:
                self.stdout.write(f"  Created commission period: {period}")

            for trader in traders:
                sales = Sale.objects.filter(
                    assigned_trader=trader,
                    sale_date__year=month_date.year,
                    sale_date__month=month_date.month,
                    is_finalized=True,
                )

                if sales.exists():
                    total_sales_value = sum(s.sale_price for s in sales)
                    total_margin = sum(s.margin_amount for s in sales)
                    total_commission = sum(
                        s.commission_amount for s in sales if s.commission_amount
                    )

                    CommissionSummary.objects.get_or_create(
                        trader=trader,
                        period=period,
                        defaults={
                            "sales_count": sales.count(),
                            "total_sales_value": total_sales_value,
                            "total_margin": total_margin,
                            "base_commission": total_commission,
                            "tier_bonus": Decimal("0"),
                            "total_commission": total_commission,
                            "payout_status": (
                                "pending" if not period.is_closed else "approved"
                            ),
                            "created_by": admin_user,
                        },
                    )
                    self.stdout.write(
                        f"    Commission summary for {trader.username} - {period}"
                    )

    def create_reports(self):
        """Create report templates and scheduled reports"""
        self.stdout.write("Creating reports...")

        admin_user = User.objects.get(username="admin")

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
                    "created_by": admin_user,
                },
            )
            if created:
                self.stdout.write(f"  Created report template: {name}")

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
                created_by=admin_user,
            )
            scheduled.recipients.set(managers)
            self.stdout.write(f"  Created scheduled report: {scheduled.name}")

        for template in templates[:3]:
            ReportExecution.objects.create(
                template=template,
                executed_by=admin_user,
                start_time=timezone.now() - timedelta(days=random.randint(1, 30)),
                end_time=timezone.now()
                - timedelta(days=random.randint(1, 30))
                + timedelta(minutes=5),
                status="completed",
                record_count=random.randint(50, 500),
                created_by=admin_user,
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
