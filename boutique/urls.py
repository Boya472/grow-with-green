from django.urls import path
from . import views

app_name = 'boutique'

urlpatterns = [
    # Catalogue
    path('', views.catalogue, name='catalogue'),
    path('recherche/', views.recherche, name='recherche'),
    
    # Produits
    path('produit/<int:pk>/', views.detail_produit, name='detail_produit'),
    
    # Panier
    path('panier/', views.voir_panier, name='voir_panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/supprimer/<int:item_id>/', views.supprimer_du_panier, name='supprimer_du_panier'),
    
    # Avis
    path('produit/<int:produit_id>/avis/', views.ajouter_avis, name='ajouter_avis'),
    path('avis/<int:avis_id>/utile/', views.marquer_utile, name='marquer_utile'),
    
    # Wishlist
    path('favoris/', views.wishlist, name='wishlist'),
    path('favoris/ajouter/<int:produit_id>/', views.ajouter_favoris, name='ajouter_favoris'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    path('notifications/', views.notifications, name='notifications'),
]