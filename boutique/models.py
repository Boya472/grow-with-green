from django.db import models
from production.models import Legume
from django.core.validators import MinValueValidator, MaxValueValidator
class Produit(models.Model):
    """
    Produits disponibles à la vente (basés sur les légumes)
    """
    legume = models.OneToOneField(
        Legume,
        on_delete=models.CASCADE,
        verbose_name="Légume"
    )
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom du produit"
    )
    description = models.TextField(
        verbose_name="Description"
    )
    image = models.ImageField(
        upload_to='products/',
        verbose_name="Image du produit"
    )
    prix_b2c = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix B2C (particuliers) par kg"
    )
    prix_b2b = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix B2B (professionnels) par kg"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Produit actif",
        help_text="Décocher pour masquer le produit de la boutique"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
    
    def __str__(self):
        return self.nom
    
    @property
    def stock_disponible(self):
        """Retourne le stock disponible pour ce produit"""
        from production.models import Stock
        try:
            stock = Stock.objects.get(legume=self.legume)
            return stock.quantite_disponible
        except Stock.DoesNotExist:
            return 0
    
    @property
    def est_disponible(self):
        """Vérifie si le produit est en stock"""
        return self.stock_disponible > 0


from production.models import Stock as ProductionStock

class Stock(ProductionStock):
    """
    Proxy pour accéder aux stocks depuis la boutique
    """
    class Meta:
        proxy = True
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"



class Panier(models.Model):
    """
    Panier d'achat des clients
    """
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name="Client"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
    
    def __str__(self):
        return f"Panier de {self.user}"
    
    @property
    def total(self):
        """Calcule le montant total du panier"""
        total = 0
        for item in self.items.all():
            total += item.sous_total
        return total
    
    @property
    def nombre_articles(self):
        """Compte le nombre d'articles dans le panier"""
        return self.items.count()


class PanierItem(models.Model):
    """
    Articles dans le panier
    """
    panier = models.ForeignKey(
        Panier,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Panier"
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
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"
        unique_together = ['panier', 'produit']
    
    def __str__(self):
        return f"{self.produit} x {self.quantite} kg"
    
    @property
    def prix_unitaire(self):
        """Retourne le prix selon le type de client"""
        if self.panier.user.user_type == 'B2B':
            return self.produit.prix_b2b
        return self.produit.prix_b2c
    
    @property
    def sous_total(self):
        """Calcule le sous-total de la ligne"""
        return self.quantite * self.prix_unitaire
    
class Avis(models.Model):
    """
    Avis et notes des clients sur les produits
    """
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name='avis',
        verbose_name="Produit"
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name="Utilisateur"
    )
    note = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note (1-5 étoiles)"
    )
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre de l'avis"
    )
    commentaire = models.TextField(
        verbose_name="Commentaire"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de publication"
    )
    verifie = models.BooleanField(
        default=False,
        verbose_name="Achat vérifié",
        help_text="L'utilisateur a acheté ce produit"
    )
    utile_count = models.IntegerField(
        default=0,
        verbose_name="Nombre de 'utile'"
    )
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-date_creation']
        unique_together = ['produit', 'user']  # Un avis par produit par utilisateur
    
    def __str__(self):
        return f"{self.user.username} - {self.produit.nom} ({self.note}⭐)"
    
    def save(self, *args, **kwargs):
        # Vérifier si l'utilisateur a acheté le produit
        from commandes.models import Commande, CommandeItem
        has_bought = CommandeItem.objects.filter(
            commande__user=self.user,
            commande__statut='LIVREE',
            produit=self.produit
        ).exists()
        self.verifie = has_bought
        super().save(*args, **kwargs)


class AvisUtile(models.Model):
    """
    Votes "utile" sur les avis
    """
    avis = models.ForeignKey(
        Avis,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE
    )
    date_vote = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vote utile"
        verbose_name_plural = "Votes utiles"
        unique_together = ['avis', 'user']
    
    def __str__(self):
        return f"{self.user.username} trouve utile l'avis de {self.avis.user.username}"


# Ajoute cette méthode à la classe Produit existante
def note_moyenne(self):
    """Calcule la note moyenne du produit"""
    from django.db.models import Avg
    avg = self.avis.aggregate(Avg('note'))['note__avg']
    return round(avg, 1) if avg else 0

def nombre_avis(self):
    """Compte le nombre d'avis"""
    return self.avis.count()

# Ajoute ces méthodes comme properties à la classe Produit
Produit.note_moyenne = property(note_moyenne)
Produit.nombre_avis = property(nombre_avis)

# Ajoute ce modèle à la fin de boutique/models.py

class Wishlist(models.Model):
    """
    Liste de souhaits / Favoris
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='wishlist',
        verbose_name="Utilisateur"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Liste de souhaits"
        verbose_name_plural = "Listes de souhaits"
    
    def __str__(self):
        return f"Wishlist de {self.user.username}"
    
    @property
    def nombre_produits(self):
        return self.produits.count()


class WishlistItem(models.Model):
    """
    Produits dans la wishlist
    """
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='produits',
        verbose_name="Liste de souhaits"
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        verbose_name="Produit"
    )
    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )
    
    class Meta:
        verbose_name = "Produit favori"
        verbose_name_plural = "Produits favoris"
        unique_together = ['wishlist', 'produit']
        ordering = ['-date_ajout']
    
    def __str__(self):
        return f"{self.produit.nom} - {self.wishlist.user.username}"