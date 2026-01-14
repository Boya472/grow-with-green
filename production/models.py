from django.db import models
from datetime import timedelta

class Legume(models.Model):
    """
    Modèle pour les 3 types de légumes cultivés
    Respecte le cahier des charges : courges, gombo, aubergines
    """
    TYPES_LEGUMES = (
        ('COURGE', 'Courge'),
        ('GOMBO', 'Gombo'),
        ('AUBERGINE', 'Aubergine'),
    )
    
    nom = models.CharField(
        max_length=50,
        choices=TYPES_LEGUMES,
        unique=True,
        verbose_name="Type de légume"
    )
    cycle_jours = models.IntegerField(
        verbose_name="Cycle de culture (jours)",
        help_text="Nombre de jours entre plantation et récolte"
    )
    description = models.TextField(
        verbose_name="Description"
    )
    
    class Meta:
        verbose_name = "Légume"
        verbose_name_plural = "Légumes"
    
    def __str__(self):
        return self.get_nom_display()


class Plantation(models.Model):
    """
    Enregistrement des plantations
    """
    legume = models.ForeignKey(
        Legume, 
        on_delete=models.CASCADE,
        verbose_name="Légume"
    )
    date_plantation = models.DateField(
        verbose_name="Date de plantation"
    )
    quantite_plantee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Quantité plantée (kg)",
        help_text="Estimation de la quantité à récolter"
    )
    date_recolte_prevue = models.DateField(
        verbose_name="Date de récolte prévue",
        blank=True,
        null=True
    )
    statut = models.CharField(
        max_length=20,
        choices=(
            ('EN_COURS', 'En cours'),
            ('RECOLTEE', 'Récoltée'),
        ),
        default='EN_COURS',
        verbose_name="Statut"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Plantation"
        verbose_name_plural = "Plantations"
        ordering = ['-date_plantation']
    
    def __str__(self):
        return f"{self.legume} - {self.date_plantation}"
    
    def save(self, *args, **kwargs):
        # Calcul automatique de la date de récolte prévue
        if not self.date_recolte_prevue and self.legume:
            self.date_recolte_prevue = self.date_plantation + timedelta(days=self.legume.cycle_jours)
        super().save(*args, **kwargs)


class Recolte(models.Model):
    """
    Enregistrement des récoltes
    """
    plantation = models.ForeignKey(
        Plantation,
        on_delete=models.CASCADE,
        related_name='recoltes',
        verbose_name="Plantation",
        blank=True,
        null=True
    )
    legume = models.ForeignKey(
        Legume,
        on_delete=models.CASCADE,
        verbose_name="Légume"
    )
    date_recolte = models.DateField(
        verbose_name="Date de récolte"
    )
    quantite_recoltee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantité récoltée (kg)"
    )
    qualite = models.CharField(
        max_length=20,
        choices=(
            ('EXCELLENTE', 'Excellente'),
            ('BONNE', 'Bonne'),
            ('MOYENNE', 'Moyenne'),
        ),
        default='BONNE',
        verbose_name="Qualité"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Récolte"
        verbose_name_plural = "Récoltes"
        ordering = ['-date_recolte']
    
    def __str__(self):
        return f"{self.legume} - {self.date_recolte} ({self.quantite_recoltee} kg)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour le statut de la plantation si elle existe
        if self.plantation:
            self.plantation.statut = 'RECOLTEE'
            self.plantation.save()
        # Mettre à jour le stock après la récolte
        from boutique.models import Stock
        stock, created = Stock.objects.get_or_create(legume=self.legume)
        stock.quantite_disponible += self.quantite_recoltee
        stock.save()


class Stock(models.Model):
    """
    Suivi des stocks en temps réel
    """
    legume = models.OneToOneField(
        Legume,
        on_delete=models.CASCADE,
        verbose_name="Légume"
    )
    quantite_disponible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Quantité disponible (kg)"
    )
    seuil_alerte = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10,
        verbose_name="Seuil d'alerte (kg)",
        help_text="Alerte quand le stock descend sous cette valeur"
    )
    date_derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
    
    def __str__(self):
        return f"Stock {self.legume} : {self.quantite_disponible} kg"
    
    @property
    def est_en_alerte(self):
        """Vérifie si le stock est en dessous du seuil d'alerte"""
        return self.quantite_disponible <= self.seuil_alerte
    
    @property
    def est_en_rupture(self):
        """Vérifie si le stock est en rupture"""
        return self.quantite_disponible <= 0