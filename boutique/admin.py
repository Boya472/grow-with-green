from django.contrib import admin
from .models import Produit, Panier, PanierItem
# Ajoute ces imports et classes à boutique/admin.py

from .models import Avis, AvisUtile, Wishlist, WishlistItem

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ['produit', 'user', 'note', 'titre', 'verifie', 'utile_count', 'date_creation']
    list_filter = ['note', 'verifie', 'date_creation']
    search_fields = ['produit__nom', 'user__username', 'titre', 'commentaire']
    readonly_fields = ['verifie', 'utile_count', 'date_creation']
    
    fieldsets = (
        ('Informations', {
            'fields': ('produit', 'user', 'note')
        }),
        ('Contenu', {
            'fields': ('titre', 'commentaire')
        }),
        ('Statistiques', {
            'fields': ('verifie', 'utile_count', 'date_creation'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AvisUtile)
class AvisUtileAdmin(admin.ModelAdmin):
    list_display = ['avis', 'user', 'date_vote']
    list_filter = ['date_vote']
    search_fields = ['avis__produit__nom', 'user__username']


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['date_ajout']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'nombre_produits', 'date_creation']
    search_fields = ['user__username', 'user__email']
    inlines = [WishlistItemInline]
    
    def nombre_produits(self, obj):
        return obj.nombre_produits
    nombre_produits.short_description = 'Nb produits'
@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'legume', 'prix_b2c', 'prix_b2b', 'stock_disponible', 'actif']
    list_filter = ['actif', 'legume']
    search_fields = ['nom', 'description']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('legume', 'nom', 'description', 'image')
        }),
        ('Tarification', {
            'fields': ('prix_b2c', 'prix_b2b')
        }),
        ('Disponibilité', {
            'fields': ('actif',)
        }),
    )

class PanierItemInline(admin.TabularInline):
    model = PanierItem
    extra = 0
    readonly_fields = ['sous_total']

@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ['user', 'nombre_articles', 'total', 'date_creation']
    search_fields = ['user__username', 'user__email']
    inlines = [PanierItemInline]
    
    def nombre_articles(self, obj):
        return obj.nombre_articles
    nombre_articles.short_description = 'Nb articles'
    
    def total(self, obj):
        return f"{obj.total} FCFA"
    total.short_description = 'Total'