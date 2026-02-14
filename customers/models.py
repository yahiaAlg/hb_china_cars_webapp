from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from core.models import BaseModel

class Customer(BaseModel):
    """Local Algerian customers"""
    
    CUSTOMER_TYPES = [
        ('individual', 'Particulier'),
        ('company', 'Entreprise'),
    ]
    
    # Algerian provinces (Wilayas) - major ones
    WILAYA_CHOICES = [
        ('01', 'Adrar'), ('02', 'Chlef'), ('03', 'Laghouat'), ('04', 'Oum El Bouaghi'),
        ('05', 'Batna'), ('06', 'Béjaïa'), ('07', 'Biskra'), ('08', 'Béchar'),
        ('09', 'Blida'), ('10', 'Bouira'), ('11', 'Tamanghasset'), ('12', 'Tébessa'),
        ('13', 'Tlemcen'), ('14', 'Tiaret'), ('15', 'Tizi Ouzou'), ('16', 'Alger'),
        ('17', 'Djelfa'), ('18', 'Jijel'), ('19', 'Sétif'), ('20', 'Saïda'),
        ('21', 'Skikda'), ('22', 'Sidi Bel Abbès'), ('23', 'Annaba'), ('24', 'Guelma'),
        ('25', 'Constantine'), ('26', 'Médéa'), ('27', 'Mostaganem'), ('28', 'M\'Sila'),
        ('29', 'Mascara'), ('30', 'Ouargla'), ('31', 'Oran'), ('32', 'El Bayadh'),
        ('33', 'Illizi'), ('34', 'Bordj Bou Arréridj'), ('35', 'Boumerdès'), ('36', 'El Tarf'),
        ('37', 'Tindouf'), ('38', 'Tissemsilt'), ('39', 'El Oued'), ('40', 'Khenchela'),
        ('41', 'Souk Ahras'), ('42', 'Tipaza'), ('43', 'Mila'), ('44', 'Aïn Defla'),
        ('45', 'Naâma'), ('46', 'Aïn Témouchent'), ('47', 'Ghardaïa'), ('48', 'Relizane'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom complet/Raison sociale")
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, verbose_name="Type de client")
    
    # Tax identification for companies
    nif_tax_id = models.CharField(
        max_length=20, blank=True, 
        verbose_name="NIF/Numéro fiscal",
        help_text="Obligatoire pour les entreprises"
    )
    
    # Contact information
    phone = models.CharField(
        max_length=20, 
        verbose_name="Téléphone",
        validators=[
            RegexValidator(
                regex=r'^(\+213|0)[1-9][0-9]{8}$',
                message="Format: +213XXXXXXXXX ou 0XXXXXXXXX"
            )
        ]
    )
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    
    # Address
    address = models.TextField(verbose_name="Adresse")
    wilaya = models.CharField(max_length=2, choices=WILAYA_CHOICES, verbose_name="Wilaya")
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_customer_type_display()})"
    
    def clean(self):
        """Validation"""
        super().clean()
        
        # NIF required for companies
        if self.customer_type == 'company' and not self.nif_tax_id:
            raise ValidationError({'nif_tax_id': 'Le NIF est obligatoire pour les entreprises.'})
        
        # Unique name or phone validation
        existing = Customer.objects.filter(
            models.Q(name__iexact=self.name) | models.Q(phone=self.phone)
        )
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        
        if existing.exists():
            raise ValidationError('Un client avec ce nom ou ce téléphone existe déjà.')
    
    @property
    def total_purchases(self):
        """Get total number of vehicle purchases"""
        return self.sale_set.count()
    
    @property
    def total_purchase_value(self):
        """Get total purchase value in DA"""
        return sum(sale.sale_price for sale in self.sale_set.all())
    
    @property
    def outstanding_balance(self):
        """Get total outstanding balance from unpaid invoices"""
        return sum(
            invoice.balance_due 
            for invoice in self.invoice_set.filter(balance_due__gt=0)
        )
    
    @property
    def last_purchase_date(self):
        """Get date of last purchase"""
        last_sale = self.sale_set.order_by('-sale_date').first()
        return last_sale.sale_date if last_sale else None
    
    def get_wilaya_display(self):
        """Get wilaya display name"""
        wilaya_dict = dict(self.WILAYA_CHOICES)
        return wilaya_dict.get(self.wilaya, self.wilaya)
    
    @property
    def is_company(self):
        return self.customer_type == 'company'
    
    @property
    def is_individual(self):
        return self.customer_type == 'individual'

class CustomerNote(BaseModel):
    """Notes and interactions with customers"""
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_notes')
    note = models.TextField(verbose_name="Note")
    is_important = models.BooleanField(default=False, verbose_name="Important")
    
    class Meta:
        verbose_name = "Note client"
        verbose_name_plural = "Notes clients"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note pour {self.customer.name} - {self.created_at.strftime('%d/%m/%Y')}"