from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Produit, Panier, PanierItem, Avis, Wishlist, WishlistItem, AvisUtile
from production.models import Stock
from django.db.models import Q, Avg, Sum, Count, Max
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.utils import timezone
import json
from decimal import Decimal
from commandes.models import Commande, CommandeItem  # Ajout de l'import
from production.models import Stock, Legume

def catalogue(request):
    """Page catalogue - tous les produits"""
    produits = Produit.objects.filter(actif=True).select_related('legume')
    
    # Filtrer uniquement les produits en stock
    produits_disponibles = [p for p in produits if p.est_disponible]
    
    # Préparer les données JSON pour le JavaScript
    produits_json = []
    for produit in produits_disponibles:
        # Récupérer l'URL de l'image
        image_url = produit.image.url if produit.image else ''
        
        # Vérifier si c'est le bon champ pour la catégorie
        # Si legume a un champ 'nom' ou 'type'
        categorie_nom = produit.legume.nom if hasattr(produit.legume, 'nom') else str(produit.legume)
        
        produits_json.append({
            'id': produit.id,
            'nom': produit.nom,
            'description': produit.description,
            'prix_b2c': float(produit.prix_b2c),
            'prix_b2b': float(produit.prix_b2b),
            'categorie': categorie_nom,
            'categorie_id': str(produit.legume.nom).lower().replace(' ', '-'),  # Format ID pour JS
            'est_disponible': produit.est_disponible,
            'stock_disponible': float(produit.stock_disponible) if produit.stock_disponible else 0,
            'stock_max': 100,  # Vous pouvez ajuster ceci si vous avez un champ stock_max
            'image': image_url,
            'note_moyenne': float(produit.note_moyenne),
            'nombre_avis': produit.nombre_avis,
            'legume_id': produit.legume.id,
        })
    
    context = {
        'produits': produits_disponibles,
        'produits_json': json.dumps(produits_json, default=str),
        'categories': Legume.objects.all(),  # Ajout des catégories pour référence
    }
    return render(request, 'boutique/catalogue.html', context)


def detail_produit(request, pk):
    """Détail d'un produit"""
    produit = get_object_or_404(Produit, pk=pk, actif=True)
    
    # Obtenir le stock
    try:
        stock = Stock.objects.get(legume=produit.legume)
    except Stock.DoesNotExist:
        stock = None
    
    # Récupérer les avis associés
    avis = produit.avis.select_related('user').order_by('-date_creation')
    
    # Calculer la note moyenne
    note_moyenne = produit.avis.aggregate(Avg('note'))['note__avg'] or 0
    
    # Récupérer les produits similaires (même catégorie)
    produits_similaires = Produit.objects.filter(
        legume=produit.legume,
        actif=True
    ).exclude(pk=pk)[:4]
    
    # Vérifier si l'utilisateur connecté a ce produit en favoris
    est_favori = False
    if request.user.is_authenticated:
        est_favori = WishlistItem.objects.filter(
            wishlist__user=request.user,
            produit=produit
        ).exists()
    
    context = {
        'produit': produit,
        'stock': stock,
        'avis': avis,
        'note_moyenne': note_moyenne,
        'produits_similaires': produits_similaires,
        'est_favori': est_favori,
    }
    return render(request, 'boutique/detail_produit.html', context)


@login_required
def ajouter_au_panier(request, produit_id):
    """Ajouter un produit au panier"""
    if request.method == 'POST':
        produit = get_object_or_404(Produit, pk=produit_id, actif=True)
        
        # Utiliser Decimal
        quantite = Decimal(request.POST.get('quantite', '1'))
        
        # Vérifier le stock disponible
        if quantite > Decimal(produit.stock_disponible):
            messages.error(request, f"Stock insuffisant. Disponible : {produit.stock_disponible} kg")
            return redirect('boutique:detail_produit', pk=produit_id)
        
        panier, created = Panier.objects.get_or_create(user=request.user)
        
        panier_item, created = PanierItem.objects.get_or_create(
            panier=panier,
            produit=produit,
            defaults={'quantite': quantite}
        )
        
        if not created:
            nouvelle_quantite = panier_item.quantite + quantite
            
            if nouvelle_quantite > Decimal(produit.stock_disponible):
                messages.error(request, f"Stock insuffisant. Disponible : {produit.stock_disponible} kg")
                return redirect('boutique:voir_panier')
            
            panier_item.quantite = nouvelle_quantite
            panier_item.save()
        
        messages.success(request, f"{produit.nom} ajouté au panier")
        return redirect('boutique:voir_panier')
    
    return redirect('boutique:catalogue')


def recherche(request):
    """Recherche avancée de produits"""
    query = request.GET.get('q', '')
    categorie = request.GET.get('categorie', '')
    prix_min = request.GET.get('prix_min', '')
    prix_max = request.GET.get('prix_max', '')
    tri = request.GET.get('tri', 'pertinence')
    
    # Base queryset
    produits = Produit.objects.filter(actif=True)
    
    # Recherche par mot-clé
    if query:
        produits = produits.filter(
            Q(nom__icontains=query) |
            Q(description__icontains=query) |
            Q(legume__nom__icontains=query)
        )
    
    # Filtre par catégorie (type de légume)
    if categorie:
        produits = produits.filter(legume__nom=categorie)
    
    # Filtre par prix
    if prix_min:
        produits = produits.filter(prix_b2c__gte=prix_min)
    if prix_max:
        produits = produits.filter(prix_b2c__lte=prix_max)
    
    # Tri
    if tri == 'prix_asc':
        produits = produits.order_by('prix_b2c')
    elif tri == 'prix_desc':
        produits = produits.order_by('-prix_b2c')
    elif tri == 'nom':
        produits = produits.order_by('nom')
    elif tri == 'note':
        produits = produits.annotate(avg_note=Avg('avis__note')).order_by('-avg_note')
    
    # Filtrer seulement les produits en stock
    produits_disponibles = [p for p in produits if p.est_disponible]
    
    # Préparer les données JSON
    produits_json = []
    for produit in produits_disponibles:
        note_moyenne = produit.avis.aggregate(Avg('note'))['note__avg'] or 0
        
        produits_json.append({
            'id': produit.id,
            'nom': produit.nom,
            'description': produit.description,
            'prix_b2c': float(produit.prix_b2c),
            'prix_b2b': float(produit.prix_b2b),
            'categorie': produit.legume.get_nom_display(),
            'categorie_id': produit.legume.nom,
            'est_disponible': produit.est_disponible,
            'stock_disponible': float(produit.stock_disponible) if produit.stock_disponible else 0,
            'image': produit.image.url if produit.image else None,
            'note_moyenne': float(note_moyenne),
        })
    
    context = {
        'produits': produits_disponibles,
        'produits_json': json.dumps(produits_json, default=str),
        'query': query,
        'nombre_resultats': len(produits_disponibles),
        'categorie': categorie,
        'prix_min': prix_min,
        'prix_max': prix_max,
        'tri': tri,
    }
    return render(request, 'boutique/recherche.html', context)


@login_required
def ajouter_avis(request, produit_id):
    """Ajouter un avis sur un produit"""
    produit = get_object_or_404(Produit, pk=produit_id)
    
    if request.method == 'POST':
        note = request.POST.get('note')
        titre = request.POST.get('titre')
        commentaire = request.POST.get('commentaire')
        
        # Vérifier si l'utilisateur a déjà donné un avis
        if Avis.objects.filter(produit=produit, user=request.user).exists():
            messages.warning(request, "Vous avez déjà donné votre avis sur ce produit")
            return redirect('boutique:detail_produit', pk=produit_id)
        
        try:
            Avis.objects.create(
                produit=produit,
                user=request.user,
                note=int(note),
                titre=titre,
                commentaire=commentaire
            )
            messages.success(request, "Merci pour votre avis !")
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
        
        return redirect('boutique:detail_produit', pk=produit_id)
    
    return redirect('boutique:detail_produit', pk=produit_id)


@login_required
def wishlist(request):
    """Voir la wishlist"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    # Préparer les données JSON
    produits_json = []
    for item in wishlist.items.all():
        produit = item.produit
        note_moyenne = produit.avis.aggregate(Avg('note'))['note__avg'] or 0
        
        produits_json.append({
            'id': produit.id,
            'nom': produit.nom,
            'description': produit.description,
            'prix_b2c': float(produit.prix_b2c),
            'prix_b2b': float(produit.prix_b2b),
            'categorie': produit.legume.get_nom_display(),
            'est_disponible': produit.est_disponible,
            'image': produit.image.url if produit.image else None,
            'note_moyenne': float(note_moyenne),
        })
    
    context = {
        'wishlist': wishlist,
        'produits_json': json.dumps(produits_json, default=str),
    }
    return render(request, 'boutique/wishlist.html', context)


@login_required
def voir_panier(request):
    """Voir le panier"""
    panier, created = Panier.objects.get_or_create(user=request.user)
    
    context = {
        'panier': panier,
    }
    return render(request, 'boutique/panier.html', context)


# Conserver les autres vues existantes...
@staff_member_required
def dashboard_admin(request):
    """Dashboard administrateur avec statistiques"""
    
    # Stats générales
    from accounts.models import User
    
    # Chiffre d'affaires total
    ca_total = Commande.objects.filter(
        paiement_valide=True
    ).aggregate(total=Sum('montant_total'))['total'] or 0
    
    # Commandes
    total_commandes = Commande.objects.count()
    commandes_mois = Commande.objects.filter(
        date_commande__month=timezone.now().month
    ).count()
    
    # Clients
    total_clients = User.objects.filter(user_type__in=['B2C', 'B2B']).count()
    nouveaux_clients = User.objects.filter(
        date_creation__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Stock
    stock_total = Stock.objects.aggregate(total=Sum('quantite_disponible'))['total'] or 0
    alertes_stock = Stock.objects.filter(est_en_alerte=True)
    
    # Ventes par mois (6 derniers mois)
    ventes_par_mois = []
    labels_mois = []
    for i in range(5, -1, -1):
        date = timezone.now() - timedelta(days=30*i)
        ventes = Commande.objects.filter(
            date_commande__month=date.month,
            date_commande__year=date.year,
            paiement_valide=True
        ).aggregate(total=Sum('montant_total'))['total'] or 0
        ventes_par_mois.append(float(ventes))
        labels_mois.append(date.strftime('%B'))
    
    # Top produits
    top_produits = CommandeItem.objects.values(
        'produit__nom'
    ).annotate(
        quantite=Sum('quantite')
    ).order_by('-quantite')[:4]
    
    produits_labels = [p['produit__nom'] for p in top_produits]
    produits_data = [float(p['quantite']) for p in top_produits]
    
    # Commandes récentes
    commandes_recentes = Commande.objects.select_related('user').order_by('-date_commande')[:10]
    
    # Top clients
    top_clients = Commande.objects.filter(
        paiement_valide=True
    ).values('user').annotate(
        total_commandes=Count('id'),
        total_depense=Sum('montant_total'),
        derniere_commande=Max('date_commande')
    ).order_by('-total_depense')[:5]
    
    # Enrichir avec les infos utilisateur
    for client in top_clients:
        client['user'] = User.objects.get(pk=client['user'])
    
    context = {
        'date_aujourdhui': timezone.now(),
        'stats': {
            'ca_total': ca_total,
            'total_commandes': total_commandes,
            'commandes_mois': commandes_mois,
            'total_clients': total_clients,
            'nouveaux_clients': nouveaux_clients,
            'stock_total': stock_total,
            'alertes_stock': alertes_stock.count(),
        },
        'ventes_labels': json.dumps(labels_mois),
        'ventes_data': json.dumps(ventes_par_mois),
        'produits_labels': json.dumps(produits_labels),
        'produits_data': json.dumps(produits_data),
        'commandes_recentes': commandes_recentes,
        'alertes_stock': alertes_stock,
        'top_clients': top_clients,
    }
    
    return render(request, 'admin/dashboard.html', context)


def index(request):
    """Page d'accueil"""
    produits_featured = Produit.objects.filter(actif=True)[:3]
    context = {
        'produits': produits_featured,
    }
    return render(request, 'index.html', context)


def about(request):
    return render(request, "about.html")


def contact(request):
    return render(request, "contact.html")


@login_required
def ajouter_favoris(request, produit_id):
    """Ajouter/Retirer un produit des favoris"""
    produit = get_object_or_404(Produit, pk=produit_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    # Vérifier si le produit est déjà dans la wishlist
    wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, produit=produit).first()
    
    if wishlist_item:
        # Retirer des favoris
        wishlist_item.delete()
        messages.success(request, f"{produit.nom} retiré des favoris")
    else:
        # Ajouter aux favoris
        WishlistItem.objects.create(wishlist=wishlist, produit=produit)
        messages.success(request, f"{produit.nom} ajouté aux favoris")
    
    return redirect(request.META.get('HTTP_REFERER', 'boutique:catalogue'))


@login_required
def marquer_utile(request, avis_id):
    """Marquer un avis comme utile"""
    avis = get_object_or_404(Avis, pk=avis_id)
    
    # Vérifier si l'utilisateur a déjà voté
    vote, created = AvisUtile.objects.get_or_create(avis=avis, user=request.user)
    
    if created:
        avis.utile_count += 1
        avis.save()
        messages.success(request, "Merci pour votre vote !")
    else:
        vote.delete()
        avis.utile_count -= 1
        avis.save()
        messages.info(request, "Vote retiré")
    
    return redirect('boutique:detail_produit', pk=avis.produit.pk)


@login_required
def supprimer_du_panier(request, item_id):
    """Supprimer un article du panier"""
    item = get_object_or_404(PanierItem, pk=item_id, panier__user=request.user)
    item.delete()
    messages.success(request, "Article supprimé du panier")
    return redirect('boutique:voir_panier')

@login_required
def mes_favoris(request):
    """Page des favoris de l'utilisateur"""
    # Récupérer ou créer la wishlist
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    # Récupérer tous les produits favoris
    produits_favoris = Produit.objects.filter(
        wishlistitem__wishlist=wishlist,
        actif=True
    ).select_related('legume')
    
    # Préparer les statistiques
    total = produits_favoris.count()
    disponibles = produits_favoris.filter(actif=True).count()
    stats = {
        'total': total,
        'disponibles': disponibles,
        'rupture': total - disponibles,
    }
    
    context = {
        'wishlist': wishlist,
        'produits_favoris': produits_favoris,
        'stats': stats,
    }
    return render(request, 'boutique/favoris.html', context)


@login_required
def notifications(request):
    """Page des notifications de l'utilisateur"""
    # Récupérer les commandes récentes
    commandes_recentes = Commande.objects.filter(
        user=request.user
    ).order_by('-date_commande')[:10]
    
    # Récupérer les avis récents sur les produits de l'utilisateur
    # (si vous avez un système de suivi de produits)
    
    # Récupérer les promotions actives
    promotions = []  # À remplir avec votre modèle de promotions si vous en avez
    
    # Compter les notifications non lues
    notifications_non_lues = 0
    
    context = {
        'commandes_recentes': commandes_recentes,
        'promotions': promotions,
        'notifications_non_lues': notifications_non_lues,
    }
    return render(request, 'accounts/notifications.html', context)


