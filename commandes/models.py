from django.db import models
from boutique.models import Produit
from django.utils import timezone

class ZoneLivraison(models.Model):
    """
    Zones de livraison en Côte d'Ivoire
    """
    nom = models.CharField(
        max_length=100,
        verbose_name="Ville/Commune"
    )
    frais_livraison = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Frais de livraison (FCFA)"
    )
    delai_livraison = models.IntegerField(
        verbose_name="Délai de livraison (jours)"
    )
    active = models.BooleanField(
        default=True,
        verbose_name="Zone active"
    )
    
    class Meta:
        verbose_name = "Zone de livraison"
        verbose_name_plural = "Zones de livraison"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} - {self.frais_livraison} FCFA"


class Commande(models.Model):
    """
    Commandes clients
    """
    STATUT_CHOICES = (
        ('EN_ATTENTE', 'En attente'),
        ('CONFIRMEE', 'Confirmée'),
        ('EN_PREPARATION', 'En préparation'),
        ('EXPEDIEE', 'Expédiée'),
        ('LIVREE', 'Livrée'),
        ('ANNULEE', 'Annulée'),
    )
    
    PAIEMENT_CHOICES = (
        ('ORANGE_MONEY', 'Orange Money'),
        ('MTN_MONEY', 'MTN Money'),
        ('MOOV_MONEY', 'Moov Money'),
        ('WAVE', 'Wave'),
        ('CARTE_BANCAIRE', 'Carte Bancaire'),
    )
    
    # Informations client
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name="Client"
    )
    
    # Numéro de commande unique
    numero_commande = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de commande"
    )
    
    # Informations de livraison
    adresse_livraison = models.TextField(
        verbose_name="Adresse de livraison"
    )
    zone_livraison = models.ForeignKey(
        ZoneLivraison,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Zone de livraison"
    )
    
    # Montants
    montant_produits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant produits (FCFA)"
    )
    frais_livraison = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Frais de livraison (FCFA)"
    )
    montant_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant total (FCFA)"
    )
    # Montant de réduction appliquée (optionnel)
    reduction = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0,
    verbose_name="Montant réduction (FCFA)"
    )

# Code promo utilisé (optionnel)
    code_promo_utilise = models.ForeignKey(
    'accounts.CodePromo',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    verbose_name="Code promo utilisé"
   )

    
    # Paiement
    mode_paiement = models.CharField(
        max_length=20,
        choices=PAIEMENT_CHOICES,
        verbose_name="Mode de paiement"
    )
    paiement_valide = models.BooleanField(
        default=False,
        verbose_name="Paiement validé"
    )
    
    # Statut et suivi
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut"
    )
    
    # Dates
    date_commande = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de commande"
    )
    date_confirmation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de confirmation"
    )
    date_expedition = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'expédition"
    )
    date_livraison = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de livraison"
    )
    
    # Notes
    notes_client = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes du client"
    )
    notes_admin = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes administrateur"
    )
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_commande']
    
    def __str__(self):
        return f"Commande {self.numero_commande} - {self.user}"
    
    def save(self, *args, **kwargs):
        # Générer un numéro de commande unique
        if not self.numero_commande:
            import uuid
            self.numero_commande = f"GWG-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculer le montant total
        self.montant_total = self.montant_produits + self.frais_livraison
        
        super().save(*args, **kwargs)
    
    def confirmer(self):
        """Confirme la commande et met à jour les stocks"""
        if self.statut == 'EN_ATTENTE' and self.paiement_valide:
            self.statut = 'CONFIRMEE'
            self.date_confirmation = timezone.now()
            self.save()
            
            # Diminuer les stocks
            from production.models import Stock
            for item in self.items.all():
                try:
                    stock = Stock.objects.get(legume=item.produit.legume)
                    stock.quantite_disponible -= item.quantite
                    stock.save()
                except Stock.DoesNotExist:
                    pass


class CommandeItem(models.Model):
    """
    Articles d'une commande
    """
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Commande"
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        verbose_name="Produit"
    )
    quantite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantité (kg)"
    )
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix unitaire (FCFA)"
    )
    sous_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Sous-total (FCFA)"
    )
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
    
    def __str__(self):
        return f"{self.produit} x {self.quantite} kg"
    
    def save(self, *args, **kwargs):
        # Calculer le sous-total
        self.sous_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)