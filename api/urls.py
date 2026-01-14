

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from . import views

# Configuration Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Grow With Green API",
        default_version='v1',
        description="""
        API REST complète pour Grow With Green - Plateforme e-commerce de légumes premium
        
        ## Authentification
        Utilisez JWT Bearer Token pour l'authentification.
        
        1. Obtenez un token: POST /api/token/
        2. Utilisez le token: Header `Authorization: Bearer {access_token}`
        
        ## Fonctionnalités
        - 🛒 Gestion produits et panier
        - 📦 Création et suivi de commandes
        - 👤 Gestion du profil utilisateur
        - ⭐ Système d'avis
        - 🎁 Programme de fidélité
        """,
        terms_of_service="https://www.growwithgreen.ci/terms/",
        contact=openapi.Contact(email="api@growwithgreen.ci"),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'legumes', views.LegumeViewSet, basename='legume')
router.register(r'produits', views.ProduitViewSet, basename='produit')
router.register(r'panier', views.PanierViewSet, basename='panier')
router.register(r'zones-livraison', views.ZoneLivraisonViewSet, basename='zone-livraison')
router.register(r'commandes', views.CommandeViewSet, basename='commande')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'auth', views.RegistrationViewSet, basename='auth')

app_name = 'api'

urlpatterns = [
    # Documentation Swagger
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Routes
    path('v1/', include(router.urls)),
]


