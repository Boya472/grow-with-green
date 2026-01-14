from django.urls import path
from . import views

app_name = 'commandes'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<str:numero_commande>/', views.confirmation, name='confirmation'),
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('detail/<str:numero_commande>/', views.detail_commande, name='detail_commande'),
    path('facture/<str:numero_commande>/', views.telecharger_facture, name='telecharger_facture'),
]