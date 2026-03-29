from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from core.models import BaseModel, Currency
from suppliers.models import Supplier
from decimal import Decimal


class Purchase(BaseModel):
    """
    Container / shipment record.
    Groups multiple vehicles imported in the same container.
    Currency and exchange rate apply to all line items.
    """

    purchase_date = models.DateField(verbose_name="Date d'achat")
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, verbose_name="Fournisseur"
    )

    # Container-level currency & exchange rate (shared by all line items)
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, verbose_name="Devise"
    )
    exchange_rate_to_da = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("0.000001"))],
        verbose_name="Taux de change vers DA",
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Achat (Conteneur)"
        verbose_name_plural = "Achats (Conteneurs)"
        ordering = ["-purchase_date"]

    def __str__(self):
        n = self.line_items.count() if self.pk else 0
        return f"Achat du {self.purchase_date} — {self.supplier.name} ({n} véhicule{'s' if n != 1 else ''})"

    def clean(self):
        super().clean()
        if self.purchase_date and self.purchase_date > timezone.now().date():
            raise ValidationError(
                {"purchase_date": "La date d'achat ne peut pas être dans le futur."}
            )
        if self.exchange_rate_to_da and self.exchange_rate_to_da <= 0:
            raise ValidationError(
                {"exchange_rate_to_da": "Le taux de change doit être supérieur à 0."}
            )

    # ── Aggregate helpers ──────────────────────────────────────────────────────

    @property
    def total_fob_da(self):
        """Sum of all line items' FOB prices in DA."""
        return sum(
            (item.fob_price_da or Decimal("0")) for item in self.line_items.all()
        )

    @property
    def purchase_price_da(self):
        """Backward-compat alias used by freight/customs forms."""
        return self.total_fob_da

    @property
    def vehicle_count(self):
        return self.line_items.count()


# ──────────────────────────────────────────────────────────────────────────────


class PurchaseLineItem(BaseModel):
    """
    One vehicle within a container/shipment.
    Captures FOB pricing and vehicle specs at the time of purchase.
    Freight and customs costs are shared across all line items in the same
    Purchase and split equally when calculating the per-vehicle landed cost.
    """

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="line_items",
        verbose_name="Achat (conteneur)",
    )
    line_number = models.PositiveIntegerField(verbose_name="N° de ligne")

    # ── Vehicle specs (known at order time) ────────────────────────────────────
    make = models.CharField(max_length=100, verbose_name="Marque")
    model = models.CharField(max_length=100, verbose_name="Modèle")
    year = models.PositiveIntegerField(verbose_name="Année")
    color = models.CharField(max_length=50, verbose_name="Couleur")
    engine_type = models.CharField(
        max_length=100, blank=True, verbose_name="Type de moteur"
    )
    vin_chassis = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="VIN / Châssis",
        help_text="Optionnel à la commande — à renseigner à la réception du véhicule.",
    )

    # ── Pricing ────────────────────────────────────────────────────────────────
    fob_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Prix FOB (devise)",
    )
    fob_price_da = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prix FOB (DA)",
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Article d'achat"
        verbose_name_plural = "Articles d'achat"
        ordering = ["purchase", "line_number"]
        unique_together = [["purchase", "line_number"]]

    def __str__(self):
        return f"#{self.line_number} — {self.make} {self.model} {self.year} ({self.purchase})"

    def save(self, *args, **kwargs):
        # Auto-assign sequential line number within the container
        if not self.line_number:
            last = (
                PurchaseLineItem.objects.filter(purchase=self.purchase)
                .order_by("-line_number")
                .values_list("line_number", flat=True)
                .first()
            )
            self.line_number = (last or 0) + 1

        # Auto-calculate DA price from container exchange rate
        if self.fob_price and self.purchase.exchange_rate_to_da:
            self.fob_price_da = self.fob_price * self.purchase.exchange_rate_to_da

        super().save(*args, **kwargs)

    # ── Shared-cost helpers ────────────────────────────────────────────────────

    @property
    def _sibling_count(self):
        """Number of vehicles in the same container (at least 1)."""
        return max(self.purchase.line_items.count(), 1)

    @property
    def freight_share_da(self):
        """This vehicle's equal share of container freight + insurance."""
        fc = getattr(self.purchase, "freight_cost", None)
        if fc and fc.total_freight_cost_da:
            return fc.total_freight_cost_da / self._sibling_count
        return Decimal("0")

    @property
    def customs_share_da(self):
        """This vehicle's equal share of customs duties + TVA."""
        cd = getattr(self.purchase, "customs_declaration", None)
        if cd and cd.total_customs_cost_da:
            return cd.total_customs_cost_da / self._sibling_count
        return Decimal("0")

    @property
    def landed_cost_da(self):
        """Total landed cost for this vehicle = FOB + freight share + customs share."""
        return (
            (self.fob_price_da or Decimal("0"))
            + self.freight_share_da
            + self.customs_share_da
        )


# ──────────────────────────────────────────────────────────────────────────────


class FreightCost(BaseModel):
    """Freight and logistics costs for the container — shared across all vehicles."""

    FREIGHT_METHODS = [("sea", "Maritime"), ("air", "Aérien")]

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
        return f"Transport {self.get_freight_method_display()} — {self.purchase}"

    def save(self, *args, **kwargs):
        freight_cost_da = self.freight_cost * self.freight_exchange_rate
        self.total_freight_cost_da = (
            freight_cost_da + self.insurance_cost_da + self.other_logistics_costs_da
        )
        super().save(*args, **kwargs)

    @property
    def cost_per_vehicle(self):
        """Freight cost per vehicle in the container."""
        n = self.purchase.vehicle_count
        if n and self.total_freight_cost_da:
            return self.total_freight_cost_da / n
        return Decimal("0")


# ──────────────────────────────────────────────────────────────────────────────


class CustomsDeclaration(BaseModel):
    """
    Customs declaration — covers the entire container.
    Duties are split equally across all vehicles in the container.
    """

    purchase = models.OneToOneField(
        Purchase, on_delete=models.CASCADE, related_name="customs_declaration"
    )
    declaration_date = models.DateField(verbose_name="Date de déclaration")
    declaration_number = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro de déclaration"
    )

    # CIF = total FOB + total freight + insurance (auto-calculated)
    cif_value_da = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Valeur CIF (DA)"
    )

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
        return f"Déclaration {self.declaration_number} — {self.purchase}"

    def clean(self):
        super().clean()
        if self.clearance_date and self.declaration_date:
            if self.clearance_date < self.declaration_date:
                raise ValidationError(
                    {
                        "clearance_date": "La date de dédouanement ne peut pas être antérieure à la déclaration."
                    }
                )

    def save(self, *args, **kwargs):
        self.total_customs_cost_da = (
            self.import_duty_da + self.tva_amount_da + self.other_fees_da
        )
        super().save(*args, **kwargs)

    def calculate_cif_value(self):
        """CIF = total FOB of all vehicles in container + freight costs."""
        purchase_price = self.purchase.total_fob_da or Decimal("0")
        freight = getattr(self.purchase, "freight_cost", None)
        freight_total = freight.total_freight_cost_da if freight else Decimal("0")
        return purchase_price + freight_total

    def auto_calculate_duties(self):
        self.import_duty_da = self.cif_value_da * (self.customs_tariff_rate / 100)
        taxable_base = self.cif_value_da + self.import_duty_da
        self.tva_amount_da = taxable_base * (self.tva_rate / 100)
        return {
            "import_duty_da": self.import_duty_da,
            "tva_amount_da": self.tva_amount_da,
            "total_customs_cost_da": self.import_duty_da
            + self.tva_amount_da
            + self.other_fees_da,
        }

    @property
    def duty_per_vehicle(self):
        n = self.purchase.vehicle_count
        if n and self.total_customs_cost_da:
            return self.total_customs_cost_da / n
        return Decimal("0")
