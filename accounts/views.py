from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from django.contrib.auth import logout
from notifications.models import Notification 
from commandes.models import Commande 

def logout_user(request):
    logout(request)
    return redirect('accounts:login')

def inscription(request):
    """Inscription pour les particuliers (B2C)"""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse', '')
        
        # Validation
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return render(request, 'accounts/inscription.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà")
            return render(request, 'accounts/inscription.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'accounts/inscription.html')
        
        # Créer l'utilisateur
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                telephone=telephone,
                adresse=adresse,
                user_type='B2C'
            )
            
            # Connexion automatique
            login(request, user)
            messages.success(request, "Compte créé avec succès ! Bienvenue chez Grow With Green !")
            return redirect('index')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du compte: {str(e)}")
            return render(request, 'accounts/inscription.html')
    
    return render(request, 'accounts/inscription.html')


def inscription_b2b(request):
    """Inscription pour les professionnels (B2B)"""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse', '')
        nom_entreprise = request.POST.get('nom_entreprise')
        secteur_activite = request.POST.get('secteur_activite')
        
        # Validation
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return render(request, 'accounts/inscription_b2b.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà")
            return render(request, 'accounts/inscription_b2b.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'accounts/inscription_b2b.html')
        
        # Créer l'utilisateur B2B
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                telephone=telephone,
                adresse=adresse,
                user_type='B2B',
                nom_entreprise=nom_entreprise,
                secteur_activite=secteur_activite,
                compte_valide=False  # Le compte B2B doit être validé par l'admin
            )
            
            messages.success(request, "Compte professionnel créé ! Il sera activé sous 24-48h après validation.")
            return redirect('accounts:login')
         
           
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du compte: {str(e)}")
            return render(request, 'accounts/inscription_b2b.html')
    
    return render(request, 'accounts/inscription_b2b.html')


@login_required
def profil(request):
    """Page de profil utilisateur"""
    if request.method == 'POST':
        # Mise à jour du profil
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.telephone = request.POST.get('telephone', user.telephone)
        user.adresse = request.POST.get('adresse', user.adresse)
        
        if user.user_type == 'B2B':
            user.nom_entreprise = request.POST.get('nom_entreprise', user.nom_entreprise)
            user.secteur_activite = request.POST.get('secteur_activite', user.secteur_activite)
        
        try:
            user.save()
            messages.success(request, "Profil mis à jour avec succès !")
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")
        
        return redirect('accounts:profil')
    
    return render(request, 'accounts/profil.html')

def login_view(request):
    """Connexion utilisateur B2C et B2B"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Vérification: Si c’est un professionnel, il doit être validé
            if user.user_type == "B2B" and not user.compte_valide:
                messages.error(request, "Votre compte professionnel n’est pas encore validé.")
                return render(request, 'accounts/login.html')

            # Connexion réussie
            login(request, user)
            return redirect('index')

        else:
            messages.error(request, "Nom d’utilisateur ou mot de passe incorrect.")
            return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')



@login_required
def notifications(request):
    """Page des notifications de l'utilisateur"""
    # Récupérer les notifications de l'utilisateur
    notifications_list = Notification.objects.filter(user=request.user).order_by('-date_creation')
    
    # Récupérer les commandes récentes
    commandes_recentes = Commande.objects.filter(
        user=request.user
    ).order_by('-date_commande')[:10]
    
    # Compter les notifications non lues
    notifications_non_lues = notifications_list.filter(lu=False).count()
    
    # Créer des notifications de démonstration si aucune
    if not notifications_list.exists():
        # Créer une notification exemple
        Notification.objects.create(
            user=request.user,
            type='INFO',
            titre='Bienvenue sur Grow With Green!',
            message='Merci de vous être inscrit. Vous recevrez ici vos notifications de commandes.',
            lien='/boutique/catalogue/'
        )
        
        # Recréer la liste
        notifications_list = Notification.objects.filter(user=request.user).order_by('-date_creation')
    
    context = {
        'notifications': notifications_list,
        'commandes_recentes': commandes_recentes,
        'notifications_non_lues': notifications_non_lues,
        'promotions': [],  # À remplir si vous avez un système de promotions
    }
    
    return render(request, 'accounts/notifications.html', context)

@login_required
def marquer_notification_lu(request, pk):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.lu = True
    notification.save()
    return redirect('accounts:notifications')

@login_required
def marquer_tout_lu(request):
    """Marquer toutes les notifications comme lues"""
    Notification.objects.filter(user=request.user, lu=False).update(lu=True)
    return redirect('accounts:notifications')