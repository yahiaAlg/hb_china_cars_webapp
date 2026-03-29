from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel, Currency

class SystemConfiguration(BaseModel):
    """System-wide configuration settings"""
    
    # Company information
    company_name = models.CharField(
        max_length=200,
        default="Bureau de Commerce Automobile Algérien",
        verbose_name="Nom de l'entreprise"
    )
    company_nif = models.CharField(
        max_length=20,
        default="123456789012345",
        verbose_name="NIF de l'entreprise"
    )
    company_address = models.TextField(
        default="Alger, Algérie",
        verbose_name="Adresse de l'entreprise"
    )
    company_phone = models.CharField(
        max_length=20,
        default="+213 21 XX XX XX",
        verbose_name="Téléphone de l'entreprise"
    )
    company_email = models.EmailField(
        default="info@bureauauto.dz",
        verbose_name="Email de l'entreprise"
    )
    
    # Default rates
    default_tva_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=19.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux TVA par défaut (%)"
    )
    default_tariff_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=25.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux tarifaire par défaut (%)"
    )
    default_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux de commission par défaut (%)"
    )
    
    # System preferences
    default_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT,
        limit_choices_to={'code': 'DA'},
        verbose_name="Devise par défaut"
    )
    reservation_duration_days = models.PositiveIntegerField(
        default=7,
        verbose_name="Durée de réservation (jours)"
    )
    invoice_due_days = models.PositiveIntegerField(
        default=30,
        verbose_name="Échéance facture (jours)"
    )
    
    # Notification settings
    enable_email_notifications = models.BooleanField(
        default=True,
        verbose_name="Activer les notifications email"
    )
    enable_overdue_alerts = models.BooleanField(
        default=True,
        verbose_name="Activer les alertes de retard"
    )
    overdue_alert_days = models.PositiveIntegerField(
        default=7,
        verbose_name="Alerte de retard après (jours)"
    )
    
    class Meta:
        verbose_name = "Configuration système"
        verbose_name_plural = "Configurations système"
    
    def __str__(self):
        return f"Configuration - {self.company_name}"
    
    @classmethod
    def get_current(cls):
        """Get current system configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config

class ExchangeRateHistory(BaseModel):
    """Historical exchange rates"""
    
    from_currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE,
        related_name='rate_history_from',
        verbose_name="Devise source"
    )
    to_currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE,
        related_name='rate_history_to',
        verbose_name="Devise cible"
    )
    rate = models.DecimalField(
        max_digits=15, decimal_places=6,
        validators=[MinValueValidator(0)],
        verbose_name="Taux de change"
    )
    effective_date = models.DateField(
        default=timezone.now,
        verbose_name="Date d'effet"
    )
    source = models.CharField(
        max_length=100, blank=True,
        verbose_name="Source du taux"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Historique des taux de change"
        verbose_name_plural = "Historiques des taux de change"
        unique_together = ['from_currency', 'to_currency', 'effective_date']
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"1 {self.from_currency.code} = {self.rate} {self.to_currency.code} ({self.effective_date})"
    
    @classmethod
    def get_latest_rate(cls, from_currency_code, to_currency_code='DA'):
        """Get latest exchange rate"""
        try:
            return cls.objects.filter(
                from_currency__code=from_currency_code,
                to_currency__code=to_currency_code,
                effective_date__lte=timezone.now().date()
            ).first()
        except cls.DoesNotExist:
            return None

class TaxRateHistory(BaseModel):
    """Historical tax rates"""
    
    TAX_TYPES = [
        ('tva', 'TVA'),
        ('tariff', 'Tarif Douanier'),
        ('other', 'Autre'),
    ]
    
    tax_type = models.CharField(
        max_length=20, choices=TAX_TYPES,
        verbose_name="Type de taxe"
    )
    rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux (%)"
    )
    effective_date = models.DateField(
        default=timezone.now,
        verbose_name="Date d'effet"
    )
    description = models.CharField(
        max_length=200, blank=True,
        verbose_name="Description"
    )
    
    class Meta:
        verbose_name = "Historique des taux de taxe"
        verbose_name_plural = "Historiques des taux de taxe"
        ordering = ['-effective_date', 'tax_type']
    
    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.rate}% ({self.effective_date})"

class UserPreference(BaseModel):
    """User-specific preferences"""
    
    THEMES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
        ('auto', 'Automatique'),
    ]
    
    LANGUAGES = [
        ('fr', 'Français'),
        ('ar', 'العربية'),
        ('en', 'English'),
    ]
    
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name="Utilisateur"
    )
    
    # Display preferences
    theme = models.CharField(
        max_length=10, choices=THEMES,
        default='light',
        verbose_name="Thème"
    )
    language = models.CharField(
        max_length=5, choices=LANGUAGES,
        default='fr',
        verbose_name="Langue"
    )
    
    # Dashboard preferences
    dashboard_widgets = models.JSONField(
        default=list,
        verbose_name="Widgets du tableau de bord"
    )
    default_page_size = models.PositiveIntegerField(
        default=20,
        verbose_name="Nombre d'éléments par page"
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications email"
    )
    browser_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications navigateur"
    )
    
    # Report preferences
    default_export_format = models.CharField(
        max_length=10,
        choices=[
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('pdf', 'PDF'),
        ],
        default='excel',
        verbose_name="Format d'export par défaut"
    )
    
    class Meta:
        verbose_name = "Préférence utilisateur"
        verbose_name_plural = "Préférences utilisateur"
    
    def __str__(self):
        return f"Préférences - {self.user.get_full_name() or self.user.username}"

class SystemLog(BaseModel):
    """System activity log"""
    
    LOG_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
        ('critical', 'Critique'),
    ]
    
    ACTION_TYPES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('system', 'Système'),
    ]
    
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Utilisateur"
    )
    
    level = models.CharField(
        max_length=10, choices=LOG_LEVELS,
        default='info',
        verbose_name="Niveau"
    )
    action_type = models.CharField(
        max_length=20, choices=ACTION_TYPES,
        verbose_name="Type d'action"
    )
    
    message = models.TextField(verbose_name="Message")
    details = models.JSONField(
        default=dict, blank=True,
        verbose_name="Détails"
    )
    
    # Request information
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    
    class Meta:
        verbose_name = "Journal système"
        verbose_name_plural = "Journaux système"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_level_display()} - {self.message[:50]}"
    
    @classmethod
    def log(cls, level, action_type, message, user=None, details=None, request=None):
        """Create a log entry"""
        log_entry = cls(
            level=level,
            action_type=action_type,
            message=message,
            user=user,
            details=details or {}
        )
        
        if request:
            log_entry.ip_address = cls.get_client_ip(request)
            log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        log_entry.save()
        return log_entry
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class BackupConfiguration(BaseModel):
    """Database backup configuration"""
    
    BACKUP_TYPES = [
        ('full', 'Sauvegarde complète'),
        ('incremental', 'Sauvegarde incrémentale'),
    ]
    
    FREQUENCIES = [
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nom de la configuration"
    )
    backup_type = models.CharField(
        max_length=20, choices=BACKUP_TYPES,
        default='full',
        verbose_name="Type de sauvegarde"
    )
    frequency = models.CharField(
        max_length=20, choices=FREQUENCIES,
        default='daily',
        verbose_name="Fréquence"
    )
    
    # Storage settings
    storage_path = models.CharField(
        max_length=500,
        verbose_name="Chemin de stockage"
    )
    max_backups_to_keep = models.PositiveIntegerField(
        default=30,
        verbose_name="Nombre max de sauvegardes à conserver"
    )
    
    # Scheduling
    next_backup = models.DateTimeField(
        verbose_name="Prochaine sauvegarde"
    )
    last_backup = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Dernière sauvegarde"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    class Meta:
        verbose_name = "Configuration de sauvegarde"
        verbose_name_plural = "Configurations de sauvegarde"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"