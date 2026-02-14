from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import BaseModel

class ReportTemplate(BaseModel):
    """Saved report templates"""
    
    REPORT_TYPES = [
        ('profit_analysis', 'Analyse de Profit'),
        ('trader_performance', 'Performance des Traders'),
        ('inventory_status', 'État du Stock'),
        ('sales_summary', 'Résumé des Ventes'),
        ('payment_status', 'État des Paiements'),
        ('commission_report', 'Rapport de Commissions'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom du rapport")
    report_type = models.CharField(
        max_length=50, choices=REPORT_TYPES,
        verbose_name="Type de rapport"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Filter parameters (stored as JSON)
    filter_parameters = models.JSONField(
        default=dict,
        verbose_name="Paramètres de filtre"
    )
    
    # Access control
    is_public = models.BooleanField(
        default=False,
        verbose_name="Rapport public"
    )
    allowed_roles = models.JSONField(
        default=list,
        verbose_name="Rôles autorisés"
    )
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'utilisations"
    )
    last_used = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Dernière utilisation"
    )
    
    class Meta:
        verbose_name = "Modèle de rapport"
        verbose_name_plural = "Modèles de rapport"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])

class ScheduledReport(BaseModel):
    """Scheduled automatic reports"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('paused', 'En pause'),
        ('disabled', 'Désactivé'),
    ]
    
    template = models.ForeignKey(
        ReportTemplate, on_delete=models.CASCADE,
        related_name='scheduled_reports',
        verbose_name="Modèle de rapport"
    )
    
    name = models.CharField(max_length=200, verbose_name="Nom de la planification")
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES,
        verbose_name="Fréquence"
    )
    
    # Recipients
    recipients = models.ManyToManyField(
        User,
        verbose_name="Destinataires"
    )
    email_subject = models.CharField(
        max_length=200,
        verbose_name="Sujet de l'email"
    )
    
    # Scheduling
    next_run = models.DateTimeField(verbose_name="Prochaine exécution")
    last_run = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Dernière exécution"
    )
    
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='active',
        verbose_name="Statut"
    )
    
    class Meta:
        verbose_name = "Rapport planifié"
        verbose_name_plural = "Rapports planifiés"
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

class ReportExecution(BaseModel):
    """Report execution log"""
    
    STATUS_CHOICES = [
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]
    
    template = models.ForeignKey(
        ReportTemplate, on_delete=models.CASCADE,
        related_name='executions',
        verbose_name="Modèle de rapport"
    )
    
    executed_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="Exécuté par"
    )
    
    start_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Heure de début"
    )
    end_time = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Heure de fin"
    )
    
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='running',
        verbose_name="Statut"
    )
    
    # Results
    record_count = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Nombre d'enregistrements"
    )
    file_path = models.CharField(
        max_length=500, blank=True,
        verbose_name="Chemin du fichier"
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Message d'erreur"
    )
    
    class Meta:
        verbose_name = "Exécution de rapport"
        verbose_name_plural = "Exécutions de rapport"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.template.name} - {self.start_time.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def duration(self):
        """Calculate execution duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def mark_completed(self, record_count=None, file_path=None):
        """Mark execution as completed"""
        self.status = 'completed'
        self.end_time = timezone.now()
        if record_count is not None:
            self.record_count = record_count
        if file_path:
            self.file_path = file_path
        self.save()
    
    def mark_failed(self, error_message):
        """Mark execution as failed"""
        self.status = 'failed'
        self.end_time = timezone.now()
        self.error_message = error_message
        self.save()