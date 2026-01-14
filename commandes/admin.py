from django.contrib import admin
from .models import ZoneLivraison, Commande, CommandeItem
from .emails import envoyer_notification_expedition, envoyer_notification_livraison
from notifications.models import Notification
@admin.register(ZoneLivraison)
class ZoneLivraisonAdmin(admin.ModelAdmin):
    list_display = ['nom', 'frais_livraison', 'delai_livraison', 'active']
    list_filter = ['active']
    search_fields = ['nom']

class CommandeItemInline(admin.TabularInline):
    model = CommandeItem
    extra = 0
    readonly_fields = ['sous_total']

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['numero_commande', 'user', 'statut', 'montant_total', 'paiement_valide', 'date_commande']
    list_filter = ['statut', 'paiement_valide', 'mode_paiement', 'date_commande']
    search_fields = ['numero_commande', 'user__username', 'user__email']
    date_hierarchy = 'date_commande'
    inlines = [CommandeItemInline]
    
    fieldsets = (
        ('Informations client', {
            'fields': ('user', 'numero_commande')
        }),
        ('Livraison', {
            'fields': ('adresse_livraison', 'zone_livraison')
        }),
        ('Montants', {
            'fields': ('montant_produits', 'frais_livraison', 'montant_total')
        }),
        ('Paiement', {
            'fields': ('mode_paiement', 'paiement_valide')
        }),
        ('Statut et suivi', {
            'fields': ('statut', 'date_confirmation', 'date_expedition', 'date_livraison')
        }),
        ('Notes', {
            'fields': ('notes_client', 'notes_admin'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['numero_commande', 'date_commande', 'montant_total']
    
    actions = ['confirmer_commandes', 'expedier_commandes']
    
    def confirmer_commandes(self, request, queryset):
        for commande in queryset:
            if commande.paiement_valide:
                commande.confirmer()
        self.message_user(request, "Commandes confirmées")
    confirmer_commandes.short_description = "Confirmer les commandes sélectionnées"
    
def expedier_commandes(self, request, queryset):
    from django.utils import timezone
    for commande in queryset:
        if commande.statut in ['CONFIRMEE', 'EN_PREPARATION']:
            commande.statut = 'EXPEDIEE'
            commande.date_expedition = timezone.now()
            commande.save()
            Notification.notifier_expedition(commande)
            # Envoyer email
            envoyer_notification_expedition(commande)
    self.message_user(request, "Commandes expédiées et emails envoyés")
expedier_commandes.short_description = "Marquer comme expédiées et notifier"