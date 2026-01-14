from django.contrib import admin
from .models import Legume, Plantation, Recolte, Stock

@admin.register(Legume)
class LegumeAdmin(admin.ModelAdmin):
    list_display = ['get_nom_display', 'cycle_jours']
    search_fields = ['nom']

@admin.register(Plantation)
class PlantationAdmin(admin.ModelAdmin):
    list_display = ['legume', 'date_plantation', 'quantite_plantee', 'date_recolte_prevue', 'statut']
    list_filter = ['statut', 'legume', 'date_plantation']
    search_fields = ['legume__nom']
    date_hierarchy = 'date_plantation'
    
    fieldsets = (
        ('Informations de plantation', {
            'fields': ('legume', 'date_plantation', 'quantite_plantee')
        }),
        ('Suivi', {
            'fields': ('date_recolte_prevue', 'statut', 'notes')
        }),
    )

@admin.register(Recolte)
class RecolteAdmin(admin.ModelAdmin):
    list_display = ['legume', 'date_recolte', 'quantite_recoltee', 'qualite', 'plantation']
    list_filter = ['qualite', 'legume', 'date_recolte']
    search_fields = ['legume__nom']
    date_hierarchy = 'date_recolte'
    
    fieldsets = (
        ('Informations de récolte', {
            'fields': ('plantation', 'legume', 'date_recolte', 'quantite_recoltee')
        }),
        ('Qualité', {
            'fields': ('qualite', 'notes')
        }),
    )

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['legume', 'quantite_disponible', 'seuil_alerte', 'est_en_alerte', 'date_derniere_mise_a_jour']
    list_filter = ['legume']
    search_fields = ['legume__nom']
    
    def est_en_alerte(self, obj):
        return obj.est_en_alerte
    est_en_alerte.boolean = True
    est_en_alerte.short_description = 'Alerte stock'