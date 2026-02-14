from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from core.models import BaseModel
from purchases.models import Purchase
from decimal import Decimal

class Vehicle(BaseModel):
    """Vehicle inventory with status tracking"""
    
    STATUS_CHOICES = [
        ('in_transit', 'En Transit'),
        ('at_customs', 'En Douane'),
        ('available', 'Disponible'),
        ('reserved', 'Réservé'),
        ('sold', 'Vendu'),
    ]
    
    # Vehicle identification
    vin_chassis = models.CharField(
        max_length=50, unique=True, 
        verbose_name="VIN/Numéro de châssis"
    )
    
    # Vehicle details
    make = models.CharField(max_length=100, verbose_name="Marque")
    model = models.CharField(max_length=100, verbose_name="Modèle")
    year = models.PositiveIntegerField(verbose_name="Année")
    color = models.CharField(max_length=50, verbose_name="Couleur")
    engine_type = models.CharField(max_length=100, blank=True, verbose_name="Type de moteur")
    specifications = models.TextField(blank=True, verbose_name="Spécifications")
    
    # Purchase information
    vehicle_purchase = models.ForeignKey(
        Purchase, on_delete=models.PROTECT, 
        related_name='vehicle_set',
        verbose_name="Achat associé"
    )
    
    # Status and availability
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, 
        default='in_transit',
        verbose_name="Statut"
    )
    
    # Reservation details (when status = 'reserved')
    reserved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='reserved_vehicles',
        verbose_name="Réservé par"
    )
    reservation_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de réservation")
    reservation_expires = models.DateTimeField(null=True, blank=True, verbose_name="Expiration réservation")
    
    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.make} {self.model} {self.year} - {self.vin_chassis}"
    
    def clean(self):
        """Validation"""
        super().clean()
        
        # VIN format validation (basic)
        if self.vin_chassis and len(self.vin_chassis) < 10:
            raise ValidationError({'vin_chassis': 'Le VIN/châssis doit contenir au moins 10 caractères.'})
        
        # Year validation
        current_year = timezone.now().year
        if self.year and (self.year < 2000 or self.year > current_year + 1):
            raise ValidationError({'year': f'L\'année doit être entre 2000 et {current_year + 1}.'})
    
    @property
    def landed_cost(self):
        """Calculate total landed cost from purchase"""
        purchase = self.vehicle_purchase
        
        # Base purchase price
        total_cost = purchase.purchase_price_da or 0
        
        # Add freight costs
        if hasattr(purchase, 'freight_cost'):
            total_cost += purchase.freight_cost.total_freight_cost_da or 0
        
        # Add customs costs
        if hasattr(purchase, 'customs_declaration'):
            total_cost += purchase.customs_declaration.total_customs_cost_da or 0
        
        return total_cost
    
    @property
    def is_available_for_sale(self):
        """Check if vehicle can be sold"""
        return self.status in ['available', 'reserved']
    
    @property
    def reservation_expired(self):
        """Check if reservation has expired"""
        if self.status != 'reserved' or not self.reservation_expires:
            return False
        return timezone.now() > self.reservation_expires
    
    def reserve_for_trader(self, trader, days=7):
        """Reserve vehicle for specific trader"""
        if self.status != 'available':
            raise ValueError("Vehicle is not available for reservation")
        
        self.status = 'reserved'
        self.reserved_by = trader
        self.reservation_date = timezone.now()
        self.reservation_expires = timezone.now() + timedelta(days=days)
        self.save()
    
    def release_reservation(self):
        """Release vehicle reservation"""
        if self.status == 'reserved':
            self.status = 'available'
            self.reserved_by = None
            self.reservation_date = None
            self.reservation_expires = None
            self.save()
    
    def mark_as_sold(self):
        """Mark vehicle as sold"""
        self.status = 'sold'
        self.reserved_by = None
        self.reservation_date = None
        self.reservation_expires = None
        self.save()
    
    @property
    def days_in_stock(self):
        """Calculate number of days in stock (since available status)"""
        if self.status not in ['available', 'reserved', 'sold']:
            return 0
        
        # Find when vehicle became available
        # For simplicity, use created_at if no better tracking available
        start_date = self.created_at.date()
        
        if self.status == 'sold':
            # Get sale date if available
            if hasattr(self, 'sale'):
                return (self.sale.sale_date - start_date).days
        
        return (timezone.now().date() - start_date).days
    
    @property
    def is_slow_moving(self, threshold_days=90):
        """Check if vehicle is slow-moving (in stock too long)"""
        return self.status == 'available' and self.days_in_stock > threshold_days

class VehiclePhoto(BaseModel):
    """Vehicle photos for documentation"""
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='vehicle_photos/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False, verbose_name="Photo principale")
    
    class Meta:
        verbose_name = "Photo de véhicule"
        verbose_name_plural = "Photos de véhicules"
    
    def __str__(self):
        return f"Photo de {self.vehicle} - {self.caption}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary photo per vehicle
        if self.is_primary:
            VehiclePhoto.objects.filter(
                vehicle=self.vehicle, is_primary=True
            ).update(is_primary=False)
        
        super().save(*args, **kwargs)

class StockAlert(BaseModel):
    """Stock alerts and notifications"""
    
    ALERT_TYPES = [
        ('slow_moving', 'Véhicule à rotation lente'),
        ('reservation_expired', 'Réservation expirée'),
        ('customs_delayed', 'Retard en douane'),
        ('low_stock', 'Stock faible'),
    ]
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Alerte de stock"
        verbose_name_plural = "Alertes de stock"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.vehicle or 'Général'}"
    
    def resolve(self, user):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()