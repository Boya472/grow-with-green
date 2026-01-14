from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.liste_notifications, name='liste'),
    path('/lire/', views.marquer_lu, name='marquer_lu'),
    path('tout-marquer-lu/', views.tout_marquer_lu, name='tout_marquer_lu'),
]