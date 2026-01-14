from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour gérer les clients B2B et B2C
    """
    TYPE_CHOICES = (
        ('B2C', 'Particulier'),
        ('B2B', 'Professionnel'),
        ('ADMIN', 'Administrateur'),
    )
    
    user_type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES, 
        default='B2C',
        verbose_name="Type d'utilisateur"
    )
    telephone = models.CharField(
        max_length=20, 
        verbose_name="Téléphone"
    )
    adresse = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Adresse"
    )
    
    # Champs spécifiques pour les clients professionnels (B2B)
    nom_entreprise = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Nom de l'entreprise"
    )
    secteur_activite = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Secteur d'activité"
    )
    compte_valide = models.BooleanField(
        default=False,
        verbose_name="Compte validé",
        help_text="Les comptes B2B doivent être validés par l'admin"
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_creation']
    
    def __str__(self):
        if self.user_type == 'B2B' and self.nom_entreprise:
            return f"{self.nom_entreprise} ({self.get_user_type_display()})"
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    def save(self, *args, **kwargs):
        # Les clients B2C sont automatiquement validés
        if self.user_type == 'B2C':
            self.compte_valide = True
        # Les admins sont toujours validés
        if self.user_type == 'ADMIN':
            self.compte_valide = True
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)
class PointsFidelite(models.Model):
    """
    Programme de fidélité avec points
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='points_fidelite',
        verbose_name="Utilisateur"
    )
    points = models.IntegerField(
        default=0,
        verbose_name="Points de fidélité"
    )
    niveau = models.CharField(
        max_length=20,
        choices=(
            ('BRONZE', 'Bronze'),
            ('ARGENT', 'Argent'),
            ('OR', 'Or'),
            ('PLATINE', 'Platine'),
        ),
        default='BRONZE',
        verbose_name="Niveau"
    )
    date_derniere_maj = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    class Meta:
        verbose_name = "Points de fidélité"
        verbose_name_plural = "Points de fidélité"
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.get_niveau_display()})"
    
    def ajouter_points(self, montant):
        """Ajoute des points basés sur le montant dépensé (1 point = 100 FCFA)"""
        nouveaux_points = int(montant / 100)
        self.points += nouveaux_points
        self.mettre_a_jour_niveau()
        self.save()
        return nouveaux_points
    
    def retirer_points(self, points):
        """Retire des points lors d'un échange"""
        if self.points >= points:
            self.points -= points
            self.mettre_a_jour_niveau()
            self.save()
            return True
        return False
    
    def mettre_a_jour_niveau(self):
        """Met à jour le niveau en fonction des points"""
        if self.points >= 10000:
            self.niveau = 'PLATINE'
        elif self.points >= 5000:
            self.niveau = 'OR'
        elif self.points >= 2000:
            self.niveau = 'ARGENT'
        else:
            self.niveau = 'BRONZE'
    
    @property
    def reduction_disponible(self):
        """Calcule la réduction disponible (1000 points = 1000 FCFA)"""
        return self.points
    
    @property
    def avantages_niveau(self):
        """Retourne les avantages du niveau actuel"""
        avantages = {
            'BRONZE': '5% de réduction sur les commandes',
            'ARGENT': '10% de réduction + livraison prioritaire',
            'OR': '15% de réduction + livraison gratuite sur Abidjan',
            'PLATINE': '20% de réduction + livraison gratuite partout + cadeaux exclusifs'
        }
        return avantages.get(self.niveau, '')


class HistoriquePoints(models.Model):
    """
    Historique des points de fidélité
    """
    TYPE_CHOICES = (
        ('GAIN', 'Gain'),
        ('DEPENSE', 'Dépense'),
        ('BONUS', 'Bonus'),
        ('EXPIRATION', 'Expiration'),
    )
    
    points_fidelite = models.ForeignKey(
        PointsFidelite,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name="Points de fidélité"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type"
    )
    points = models.IntegerField(
        verbose_name="Points"
    )
    description = models.CharField(
        max_length=500,
        verbose_name="Description"
    )
    commande = models.ForeignKey(
        'commandes.Commande',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Commande"
    )
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date"
    )
    
    class Meta:
        verbose_name = "Historique de points"
        verbose_name_plural = "Historique des points"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.points_fidelite.user.username} - {self.type} {self.points} points"


class CodePromo(models.Model):
    """
    Codes promotionnels
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code promo"
    )
    description = models.CharField(
        max_length=200,
        verbose_name="Description"
    )
    type_reduction = models.CharField(
        max_length=20,
        choices=(
            ('POURCENTAGE', 'Pourcentage'),
            ('MONTANT', 'Montant fixe'),
        ),
        default='POURCENTAGE',
        verbose_name="Type de réduction"
    )
    valeur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valeur",
        help_text="Pourcentage (ex: 10 pour 10%) ou montant en FCFA"
    )
    montant_minimum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Montant minimum",
        help_text="Montant minimum de commande pour utiliser le code"
    )
    date_debut = models.DateTimeField(
        verbose_name="Date de début"
    )
    date_fin = models.DateTimeField(
        verbose_name="Date de fin"
    )
    nombre_utilisations = models.IntegerField(
        default=0,
        verbose_name="Nombre d'utilisations"
    )
    max_utilisations = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Maximum d'utilisations",
        help_text="Laisser vide pour illimité"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    class Meta:
        verbose_name = "Code promo"
        verbose_name_plural = "Codes promo"
        ordering = ['-date_debut']
    
    def __str__(self):
        return self.code
    
    def est_valide(self, montant_commande=None):
        """Vérifie si le code promo est valide"""
        from django.utils import timezone
        now = timezone.now()
        
        # Vérifier si actif
        if not self.actif:
            return False, "Code promo désactivé"
        
        # Vérifier les dates
        if now < self.date_debut:
            return False, "Code promo pas encore actif"
        if now > self.date_fin:
            return False, "Code promo expiré"
        
        # Vérifier le nombre d'utilisations
        if self.max_utilisations and self.nombre_utilisations >= self.max_utilisations:
            return False, "Code promo épuisé"
        
        # Vérifier le montant minimum
        if montant_commande and montant_commande < self.montant_minimum:
            return False, f"Montant minimum requis : {self.montant_minimum} FCFA"
        
        return True, "Code promo valide"
    
    def calculer_reduction(self, montant):
        """Calcule le montant de la réduction"""
        if self.type_reduction == 'POURCENTAGE':
            return montant * (self.valeur / 100)
        else:
            return min(self.valeur, montant)  # Ne pas dépasser le montant total
    
    def utiliser(self):
        """Incrémente le nombre d'utilisations"""
        self.nombre_utilisations += 1
        self.save()        