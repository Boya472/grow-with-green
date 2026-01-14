

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from boutique.models import Produit, Panier, PanierItem, Avis
from production.models import Legume, Stock
from commandes.models import Commande, ZoneLivraison
from accounts.models import User, PointsFidelite

from .serializers import (
    LegumeSerializer, StockSerializer,
    ProduitListSerializer, ProduitDetailSerializer, AvisSerializer,
    PanierSerializer, PanierItemSerializer,
    CommandeListSerializer, CommandeDetailSerializer, CommandeCreateSerializer,
    ZoneLivraisonSerializer, UserSerializer, UserRegistrationSerializer,
    PointsFideliteSerializer
)


# ============================================
# ViewSets Produits
# ============================================

class LegumeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les légumes (lecture seule)
    """
    queryset = Legume.objects.all()
    serializer_class = LegumeSerializer
    permission_classes = [AllowAny]


class ProduitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les produits
    
    list: Retourne la liste des produits actifs
    retrieve: Retourne le détail d'un produit
    """
    queryset = Produit.objects.filter(actif=True)
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['legume', 'actif']
    search_fields = ['nom', 'description']
    ordering_fields = ['prix_b2c', 'nom', 'date_creation']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProduitDetailSerializer
        return ProduitListSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def ajouter_avis(self, request, pk=None):
        """Ajouter un avis sur un produit"""
        produit = self.get_object()
        
        # Vérifier si l'utilisateur a déjà donné un avis
        if Avis.objects.filter(produit=produit, user=request.user).exists():
            return Response(
                {'error': 'Vous avez déjà donné votre avis sur ce produit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AvisSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, produit=produit)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def en_stock(self, request):
        """Retourne uniquement les produits en stock"""
        produits = [p for p in self.get_queryset() if p.est_disponible]
        serializer = self.get_serializer(produits, many=True)
        return Response(serializer.data)


# ============================================
# ViewSets Panier
# ============================================

class PanierViewSet(viewsets.ViewSet):
    """
    API endpoint pour le panier
    
    list: Retourne le panier de l'utilisateur
    add_item: Ajoute un produit au panier
    remove_item: Retire un produit du panier
    clear: Vide le panier
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Voir le panier"""
        panier, created = Panier.objects.get_or_create(user=request.user)
        serializer = PanierSerializer(panier)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Ajouter un produit au panier"""
        panier, created = Panier.objects.get_or_create(user=request.user)
        
        produit_id = request.data.get('produit_id')
        quantite = float(request.data.get('quantite', 1))
        
        try:
            produit = Produit.objects.get(pk=produit_id, actif=True)
        except Produit.DoesNotExist:
            return Response(
                {'error': 'Produit non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier le stock
        if quantite > produit.stock_disponible:
            return Response(
                {'error': f'Stock insuffisant. Disponible: {produit.stock_disponible} kg'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ajouter ou mettre à jour
        item, created = PanierItem.objects.get_or_create(
            panier=panier,
            produit=produit,
            defaults={'quantite': quantite}
        )
        
        if not created:
            nouvelle_quantite = item.quantite + quantite
            if nouvelle_quantite > produit.stock_disponible:
                return Response(
                    {'error': f'Stock insuffisant. Disponible: {produit.stock_disponible} kg'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.quantite = nouvelle_quantite
            item.save()
        
        serializer = PanierSerializer(panier)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Retirer un produit du panier"""
        panier = get_object_or_404(Panier, user=request.user)
        item_id = request.data.get('item_id')
        
        try:
            item = PanierItem.objects.get(pk=item_id, panier=panier)
            item.delete()
            serializer = PanierSerializer(panier)
            return Response(serializer.data)
        except PanierItem.DoesNotExist:
            return Response(
                {'error': 'Article non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Vider le panier"""
        panier = get_object_or_404(Panier, user=request.user)
        panier.items.all().delete()
        serializer = PanierSerializer(panier)
        return Response(serializer.data)


# ============================================
# ViewSets Commandes
# ============================================

class ZoneLivraisonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les zones de livraison (lecture seule)
    """
    queryset = ZoneLivraison.objects.filter(active=True)
    serializer_class = ZoneLivraisonSerializer
    permission_classes = [AllowAny]


class CommandeViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les commandes
    
    list: Liste les commandes de l'utilisateur
    retrieve: Détail d'une commande
    create: Créer une nouvelle commande
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les commandes de l'utilisateur"""
        return Commande.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CommandeCreateSerializer
        elif self.action == 'retrieve':
            return CommandeDetailSerializer
        return CommandeListSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer une commande à partir du panier"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            commande = serializer.save()
            
            # Créer notification
            from notifications.models import Notification
            Notification.notifier_nouvelle_commande(commande)
            
            # Envoyer email
            from commandes.emails import envoyer_confirmation_commande
            envoyer_confirmation_commande(commande)
            
            detail_serializer = CommandeDetailSerializer(commande)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        
        except Panier.DoesNotExist:
            return Response(
                {'error': 'Panier vide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retourne les 5 dernières commandes"""
        commandes = self.get_queryset().order_by('-date_commande')[:5]
        serializer = self.get_serializer(commandes, many=True)
        return Response(serializer.data)


# ============================================
# ViewSets Utilisateur
# ============================================

class UserViewSet(viewsets.GenericViewSet):
    """
    API endpoint pour les utilisateurs
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retourne les informations de l'utilisateur connecté"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Met à jour le profil de l'utilisateur"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def fidelite(self, request):
        """Retourne les points de fidélité"""
        points, created = PointsFidelite.objects.get_or_create(user=request.user)
        serializer = PointsFideliteSerializer(points)
        return Response(serializer.data)


class RegistrationViewSet(viewsets.GenericViewSet):
    """
    API endpoint pour l'inscription
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Inscription d'un nouvel utilisateur"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Générer token JWT
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)