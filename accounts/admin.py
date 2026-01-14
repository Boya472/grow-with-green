from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

from .models import PointsFidelite, HistoriquePoints, CodePromo

@admin.register(PointsFidelite)
class PointsFideliteAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'niveau', 'date_derniere_maj']
    list_filter = ['niveau']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['date_derniere_maj']

@admin.register(HistoriquePoints)
class HistoriquePointsAdmin(admin.ModelAdmin):
    list_display = ['points_fidelite', 'type', 'points', 'description', 'date']
    list_filter = ['type', 'date']
    search_fields = ['points_fidelite__user__username', 'description']

@admin.register(CodePromo)
class CodePromoAdmin(admin.ModelAdmin):
    list_display = ['code', 'type_reduction', 'valeur', 'date_debut', 'date_fin', 'actif', 'nombre_utilisations']
    list_filter = ['type_reduction', 'actif', 'date_debut']
    search_fields = ['code', 'description']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'compte_valide', 'telephone', 'date_creation']
    list_filter = ['user_type', 'compte_valide', 'is_active']
    search_fields = ['username', 'email', 'nom_entreprise', 'telephone']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('user_type', 'telephone', 'adresse', 'compte_valide')
        }),
        ('Informations professionnelles (B2B)', {
            'fields': ('nom_entreprise', 'secteur_activite'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('user_type', 'telephone', 'adresse', 'email')
        }),
    )
    
    actions = ['valider_comptes', 'invalider_comptes']
    
    def valider_comptes(self, request, queryset):
        queryset.update(compte_valide=True)
        self.message_user(request, "Comptes validés avec succès")
    valider_comptes.short_description = "Valider les comptes sélectionnés"
    
    def invalider_comptes(self, request, queryset):
        queryset.update(compte_valide=False)
        self.message_user(request, "Comptes invalidés")
    invalider_comptes.short_description = "Invalider les comptes sélectionnés"