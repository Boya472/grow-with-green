from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('inscription/b2b/', views.inscription_b2b, name='inscription_b2b'),
    path('connexion/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('deconnexion/', views.logout_user, name='logout'),
    path('profil/', views.profil, name='profil'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/marquer-lu/<int:pk>/', views.marquer_notification_lu, name='marquer_lu'),
    path('notifications/marquer-tout-lu/', views.marquer_tout_lu, name='marquer_tout_lu'),
]