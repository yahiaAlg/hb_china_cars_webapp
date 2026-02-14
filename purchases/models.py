from datetime import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from core.models import BaseModel, Currency
from core.utils import CurrencyConverter, TaxCalculator
from suppliers.models import Supplier


class Purchase(BaseModel):
    """Vehicle purchase records from suppliers"""

    purchase_date = models.DateField(verbose_name="Date d'achat")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

    # FOB Price (Free On Board - price before shipping)
    purchase_price_fob = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix FOB",
    )
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    exchange_rate_to_da = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(0)],
        verbose_name="Taux de change vers DA",
    )
    purchase_price_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prix d'achat en DA",
    )

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        ordering = ["-purchase_date"]

    def __str__(self):
        return f"Achat du {self.purchase_date} - {self.supplier.name}"

    def clean(self):
        """Validation"""
        super().clean()

        if self.purchase_date and self.purchase_date > timezone.now().date():
            raise ValidationError(
                {"purchase_date": "La date d'achat ne peut pas être dans le futur."}
            )

        if self.exchange_rate_to_da and self.exchange_rate_to_da <= 0:
            raise ValidationError(
                {"exchange_rate_to_da": "Le taux de change doit être supérieur à 0."}
            )

    def save(self, *args, **kwargs):
        # Auto-calculate DA price
        if self.purchase_price_fob and self.exchange_rate_to_da:
            self.purchase_price_da = self.purchase_price_fob * self.exchange_rate_to_da

        super().save(*args, **kwargs)


class FreightCost(BaseModel):
    """Freight and logistics costs for vehicle shipping"""

    FREIGHT_METHODS = [
        ("sea", "Maritime"),
        ("air", "Aérien"),
    ]

    purchase = models.OneToOneField(
        Purchase, on_delete=models.CASCADE, related_name="freight_cost"
    )

    freight_method = models.CharField(
        max_length=10, choices=FREIGHT_METHODS, verbose_name="Mode de transport"
    )
    freight_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Coût de fret",
    )
    freight_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="freight_costs",
        verbose_name="Devise du fret",
    )
    freight_exchange_rate = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(0)],
        default=1,
        verbose_name="Taux de change du fret",
    )

    insurance_cost_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Coût d'assurance (DA)",
    )
    other_logistics_costs_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Autres frais logistiques (DA)",
    )

    total_freight_cost_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total des frais de transport (DA)",
    )

    class Meta:
        verbose_name = "Coût de transport"
        verbose_name_plural = "Coûts de transport"

    def __str__(self):
        return f"Transport {self.get_freight_method_display()} - {self.purchase}"

    def save(self, *args, **kwargs):
        # Calculate total freight cost in DA
        freight_cost_da = self.freight_cost * self.freight_exchange_rate
        self.total_freight_cost_da = (
            freight_cost_da + self.insurance_cost_da + self.other_logistics_costs_da
        )

        super().save(*args, **kwargs)


class CustomsDeclaration(BaseModel):
    """Customs declaration and duty calculation"""

    purchase = models.OneToOneField(
        Purchase, on_delete=models.CASCADE, related_name="customs_declaration"
    )

    declaration_date = models.DateField(verbose_name="Date de déclaration")
    declaration_number = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro de déclaration"
    )

    # CIF Value (Cost, Insurance, Freight)
    cif_value_da = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Valeur CIF (DA)"
    )

    # Tariffs and Duties
    customs_tariff_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux tarifaire douanier (%)",
    )
    import_duty_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Droit d'importation (DA)",
    )

    # TVA
    tva_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux TVA (%)",
    )
    tva_amount_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant TVA (DA)",
    )

    other_fees_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Autres frais douaniers (DA)",
    )

    total_customs_cost_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total des frais douaniers (DA)",
    )

    is_cleared = models.BooleanField(default=False, verbose_name="Dédouané")
    clearance_date = models.DateField(
        null=True, blank=True, verbose_name="Date de dédouanement"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Déclaration douanière"
        verbose_name_plural = "Déclarations douanières"
        ordering = ["-declaration_date"]

    def __str__(self):
        return f"Déclaration {self.declaration_number} - {self.purchase}"

    def clean(self):
        """Validation"""
        super().clean()

        if self.clearance_date and self.declaration_date:
            if self.clearance_date < self.declaration_date:
                raise ValidationError(
                    {
                        "clearance_date": "La date de dédouanement ne peut pas être antérieure à la déclaration."
                    }
                )

    def save(self, *args, **kwargs):
        # Calculate total customs cost
        self.total_customs_cost_da = (
            self.import_duty_da + self.tva_amount_da + self.other_fees_da
        )

        super().save(*args, **kwargs)

    def calculate_cif_value(self):
        """Auto-calculate CIF value from purchase and freight costs"""
        purchase_price = self.purchase.purchase_price_da or 0
        freight_cost = getattr(self.purchase, "freight_cost", None)
        freight_total = freight_cost.total_freight_cost_da if freight_cost else 0

        return purchase_price + freight_total

    def auto_calculate_duties(self):
        """Auto-calculate import duty and TVA"""
        # Import Duty = CIF Value × Tariff Rate
        self.import_duty_da = self.cif_value_da * (self.customs_tariff_rate / 100)

        # TVA = (CIF Value + Import Duty) × TVA Rate
        taxable_base = self.cif_value_da + self.import_duty_da
        self.tva_amount_da = taxable_base * (self.tva_rate / 100)

        return {
            "import_duty_da": self.import_duty_da,
            "tva_amount_da": self.tva_amount_da,
            "total_customs_cost_da": self.import_duty_da
            + self.tva_amount_da
            + self.other_fees_da,
        }
