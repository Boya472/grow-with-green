from rest_framework import serializers
from boutique.models import Produit, Panier, PanierItem, Avis
from production.models import Legume, Stock
from commandes.models import Commande, CommandeItem, ZoneLivraison
from accounts.models import User, PointsFidelite


# ============================================
# Serializers Légumes & Stock
# ============================================

class LegumeSerializer(serializers.ModelSerializer):
    """Serializer pour les légumes"""
    class Meta:
        model = Legume
        fields = ['id', 'nom', 'cycle_jours', 'description']


class StockSerializer(serializers.ModelSerializer):
    """Serializer pour les stocks"""
    legume = LegumeSerializer(read_only=True)
    
    class Meta:
        model = Stock
        fields = ['id', 'legume', 'quantite_disponible', 'seuil_alerte', 
                  'est_en_alerte', 'est_en_rupture', 'date_derniere_mise_a_jour']
        read_only_fields = ['date_derniere_mise_a_jour']


# ============================================
# Serializers Produits
# ============================================

class AvisSerializer(serializers.ModelSerializer):
    """Serializer pour les avis"""
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Avis
        fields = ['id', 'user', 'note', 'titre', 'commentaire', 
                  'date_creation', 'verifie', 'utile_count']
        read_only_fields = ['user', 'verifie', 'utile_count', 'date_creation']


class ProduitListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des produits (léger)"""
    legume = serializers.StringRelatedField()
    stock_disponible = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    note_moyenne = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)
    
    class Meta:
        model = Produit
        fields = ['id', 'nom', 'legume', 'prix_b2c', 'prix_b2b', 
                  'image', 'stock_disponible', 'note_moyenne', 'actif']


class ProduitDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail d'un produit (complet)"""
    legume = LegumeSerializer(read_only=True)
    stock_disponible = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    note_moyenne = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)
    nombre_avis = serializers.IntegerField(read_only=True)
    avis = AvisSerializer(many=True, read_only=True)
    
    class Meta:
        model = Produit
        fields = ['id', 'nom', 'legume', 'description', 'prix_b2c', 'prix_b2b',
                  'image', 'stock_disponible', 'note_moyenne', 'nombre_avis', 
                  'avis', 'actif', 'date_creation', 'date_modification']


# ============================================
# Serializers Panier
# ============================================

class PanierItemSerializer(serializers.ModelSerializer):
    """Serializer pour les items du panier"""
    produit = ProduitListSerializer(read_only=True)
    produit_id = serializers.IntegerField(write_only=True)
    prix_unitaire = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    sous_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = PanierItem
        fields = ['id', 'produit', 'produit_id', 'quantite', 
                  'prix_unitaire', 'sous_total', 'date_ajout']
        read_only_fields = ['date_ajout']


class PanierSerializer(serializers.ModelSerializer):
    """Serializer pour le panier"""
    items = PanierItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    nombre_articles = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Panier
        fields = ['id', 'items', 'total', 'nombre_articles', 
                  'date_creation', 'date_modification']


# ============================================
# Serializers Commandes
# ============================================

class ZoneLivraisonSerializer(serializers.ModelSerializer):
    """Serializer pour les zones de livraison"""
    class Meta:
        model = ZoneLivraison
        fields = ['id', 'nom', 'frais_livraison', 'delai_livraison', 'active']


class CommandeItemSerializer(serializers.ModelSerializer):
    """Serializer pour les items de commande"""
    produit = ProduitListSerializer(read_only=True)
    
    class Meta:
        model = CommandeItem
        fields = ['id', 'produit', 'quantite', 'prix_unitaire', 'sous_total']


class CommandeListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des commandes (léger)"""
    zone_livraison = serializers.StringRelatedField()
    
    class Meta:
        model = Commande
        fields = ['id', 'numero_commande', 'statut', 'montant_total', 
                  'zone_livraison', 'date_commande', 'paiement_valide']


class CommandeDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail d'une commande (complet)"""
    items = CommandeItemSerializer(many=True, read_only=True)
    zone_livraison = ZoneLivraisonSerializer(read_only=True)
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Commande
        fields = ['id', 'numero_commande', 'user', 'adresse_livraison', 
                  'zone_livraison', 'montant_produits', 'frais_livraison', 
                  'montant_total', 'mode_paiement', 'paiement_valide', 'statut',
                  'date_commande', 'date_confirmation', 'date_expedition', 
                  'date_livraison', 'notes_client', 'items']
        read_only_fields = ['numero_commande', 'user', 'date_commande']


class CommandeCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une commande"""
    zone_livraison_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Commande
        fields = ['adresse_livraison', 'zone_livraison_id', 
                  'mode_paiement', 'notes_client']
    
    def create(self, validated_data):
        """Créer une commande à partir du panier"""
        user = self.context['request'].user
        zone_id = validated_data.pop('zone_livraison_id')
        
        # Récupérer la zone
        zone = ZoneLivraison.objects.get(pk=zone_id, active=True)
        
        # Récupérer le panier
        panier = Panier.objects.get(user=user)
        
        # Créer la commande
        commande = Commande.objects.create(
            user=user,
            zone_livraison=zone,
            montant_produits=panier.total,
            frais_livraison=zone.frais_livraison,
            **validated_data
        )
        
        # Créer les items
        for item in panier.items.all():
            CommandeItem.objects.create(
                commande=commande,
                produit=item.produit,
                quantite=item.quantite,
                prix_unitaire=item.prix_unitaire
            )
        
        # Vider le panier
        panier.items.all().delete()
        
        return commande


# ============================================
# Serializers Utilisateur
# ============================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'telephone', 'user_type', 'compte_valide']
        read_only_fields = ['compte_valide']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 
                  'first_name', 'last_name', 'telephone', 'user_type']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PointsFideliteSerializer(serializers.ModelSerializer):
    """Serializer pour les points de fidélité"""
    user = serializers.StringRelatedField()
    avantages = serializers.CharField(source='avantages_niveau', read_only=True)
    
    class Meta:
        model = PointsFidelite
        fields = ['id', 'user', 'points', 'niveau', 'avantages', 
                  'reduction_disponible', 'date_derniere_maj']
        read_only_fields = ['user', 'niveau', 'date_derniere_maj']