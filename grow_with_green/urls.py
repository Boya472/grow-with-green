from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from boutique import views as boutique_views


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Page d'accueil
    path('', boutique_views.index, name='index'),
    path('admin/dashboard/', boutique_views.dashboard_admin, name='admin_dashboard'),
    path('a-propos/', boutique_views.about, name='about'),
    path('contact/', boutique_views.contact, name='contact'),
    path('notifications/', include('notifications.urls')),
    # Apps URLs
    path('boutique/', include('boutique.urls')),
    path('commandes/', include('commandes.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/', include('api.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)