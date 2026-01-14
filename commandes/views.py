from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from boutique.models import Panier
from .models import Commande, CommandeItem, ZoneLivraison
from .emails import envoyer_confirmation_commande
from notifications.models import Notification
from accounts.models import PointsFidelite, HistoriquePoints
from .pdf import generer_facture_pdf
from accounts.models import CodePromo

@login_required
def telecharger_facture(request, numero_commande):
    """Télécharger la facture en PDF"""
    commande = get_object_or_404(Commande, numero_commande=numero_commande, user=request.user)
    
    # Générer et retourner le PDF
    return generer_facture_pdf(commande)
@login_required
def checkout(request):
    """Page de checkout (finalisation de commande)"""
    # Récupérer le panier de l'utilisateur
    try:
        panier = Panier.objects.get(user=request.user)
    except Panier.DoesNotExist:
        messages.warning(request, "Votre panier est vide")
        return redirect('boutique:catalogue')
    
    if not panier.items.exists():
        messages.warning(request, "Votre panier est vide")
        return redirect('boutique:catalogue')
    
    if request.method == 'POST':
        
        # Récupérer les données du formulaire
        adresse_livraison = request.POST.get('adresse_livraison')
        zone_id = request.POST.get('zone_livraison')
        mode_paiement = request.POST.get('mode_paiement')
        notes_client = request.POST.get('notes_client', '')
        
        # Validation
        if not all([adresse_livraison, zone_id, mode_paiement]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires")
            return render(request, 'commandes/checkout.html', {'panier': panier})
        
        try:
            zone = ZoneLivraison.objects.get(pk=zone_id, active=True)
        except ZoneLivraison.DoesNotExist:
            messages.error(request, "Zone de livraison invalide")
            return render(request, 'commandes/checkout.html', {'panier': panier})
        
        # --- CODE PROMO À AJOUTER ICI ---
        code_promo_str = request.POST.get('code_promo', '')
        reduction = 0
        
        if code_promo_str:
            try:
                code_promo = CodePromo.objects.get(code=code_promo_str)
                est_valide, message = code_promo.est_valide(panier.total)
                
                if est_valide:
                    reduction = code_promo.calculer_reduction(panier.total)
                    code_promo.utiliser()
                else:
                    messages.warning(request, message)
            except CodePromo.DoesNotExist:
                messages.error(request, "Code promo invalide")
        
        # Calculer le montant final des produits
        montant_produits = panier.total - reduction
        # --- FIN DU CODE PROMO ---
        
        # Créer la commande (MODIFIER CETTE LIGNE)
        try:
            commande = Commande.objects.create(
                user=request.user,
                adresse_livraison=adresse_livraison,
                zone_livraison=zone,
                montant_produits=montant_produits,  # ICI: utiliser montant_produits au lieu de panier.total
                frais_livraison=zone.frais_livraison,
                mode_paiement=mode_paiement,
                notes_client=notes_client,
                paiement_valide=False,
                statut='EN_ATTENTE',
                reduction=reduction  # AJOUTER CETTE LIGNE si vous avez ce champ dans votre modèle
            )
            
            # Ajoutez aussi le code promo utilisé à la commande
            if code_promo_str and reduction > 0:
                commande.code_promo_utilise = code_promo  # Assurez-vous d'avoir ce champ dans Commande
                commande.save()
            
            Notification.notifier_nouvelle_commande(commande)
            envoyer_confirmation_commande(commande)
            
            # Calcul des points de fidélité sur le montant APRÈS réduction
            points_fidelite, created = PointsFidelite.objects.get_or_create(user=request.user)
            points_gagnes = points_fidelite.ajouter_points(commande.montant_total)
            
            # Historique
            HistoriquePoints.objects.create(
                points_fidelite=points_fidelite,
                type='GAIN',
                points=points_gagnes,
                description=f"Commande {commande.numero_commande}",
                commande=commande
            )
            
            # Créer les items de commande
            for item in panier.items.all():
                CommandeItem.objects.create(
                    commande=commande,
                    produit=item.produit,
                    quantite=item.quantite,
                    prix_unitaire=item.prix_unitaire
                )
            
            # Vider le panier
            panier.items.all().delete()
            
            messages.success(request, f"Commande {commande.numero_commande} créée avec succès !")
            return redirect('commandes:confirmation', numero_commande=commande.numero_commande)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de la commande: {str(e)}")
            return render(request, 'commandes/checkout.html', {'panier': panier})
    
    # Pour les requêtes GET, afficher la page de checkout
    context = {
        'panier': panier,
    }
    return render(request, 'commandes/checkout.html', context)


@login_required
def confirmation(request, numero_commande):
    """Page de confirmation de commande"""
    commande = get_object_or_404(Commande, numero_commande=numero_commande, user=request.user)
    
    context = {
        'commande': commande,
    }
    return render(request, 'commandes/confirmation.html', context)


@login_required
def mes_commandes(request):
    """Liste des commandes de l'utilisateur"""
    commandes = Commande.objects.filter(user=request.user).order_by('-date_commande')
    
    context = {
        'commandes': commandes,
    }
    return render(request, 'commandes/mes_commandes.html', context)


@login_required
def detail_commande(request, numero_commande):
    """Détail d'une commande"""
    commande = get_object_or_404(Commande, numero_commande=numero_commande, user=request.user)
    
    context = {
        'commande': commande,
    }
    return render(request, 'commandes/detail_commande.html', context)