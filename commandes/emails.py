from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def envoyer_confirmation_commande(commande):
    """Envoie un email de confirmation de commande"""
    subject = f"Commande {commande.numero_commande} confirmée - Grow With Green"
    
    message = f"""
    Bonjour {commande.user.get_full_name()},
    
    Votre commande {commande.numero_commande} a été confirmée avec succès !
    
    Détails de la commande :
    - Montant total : {commande.montant_total} FCFA
    - Zone de livraison : {commande.zone_livraison.nom}
    - Mode de paiement : {commande.get_mode_paiement_display()}
    
    Articles commandés :
    """
    
    for item in commande.items.all():
        message += f"- {item.produit.nom} : {item.quantite} kg x {item.prix_unitaire} FCFA\n"
    
    message += f"""
    
    Votre commande sera préparée et expédiée sous 24h.
    
    Vous pouvez suivre votre commande en ligne : http://127.0.0.1:8000/commandes/detail/{commande.numero_commande}/
    
    Merci de votre confiance !
    
    L'équipe Grow With Green
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [commande.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur envoi email : {e}")
        return False


def envoyer_notification_expedition(commande):
    """Envoie un email quand la commande est expédiée"""
    subject = f"Votre commande {commande.numero_commande} a été expédiée !"
    
    message = f"""
    Bonjour {commande.user.get_full_name()},
    
    Bonne nouvelle ! Votre commande {commande.numero_commande} a été expédiée.
    
    Détails de livraison :
    - Destination : {commande.zone_livraison.nom}
    - Délai estimé : {commande.zone_livraison.delai_livraison} jour(s)
    - Adresse : {commande.adresse_livraison}
    
    Suivez votre commande : http://127.0.0.1:8000/commandes/detail/{commande.numero_commande}/
    
    Cordialement,
    L'équipe Grow With Green
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [commande.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur envoi email : {e}")
        return False


def envoyer_notification_livraison(commande):
    """Envoie un email quand la commande est livrée"""
    subject = f"Votre commande {commande.numero_commande} est livrée ! 🎉"
    
    message = f"""
    Bonjour {commande.user.get_full_name()},
    
    Votre commande {commande.numero_commande} a été livrée avec succès !
    
    Nous espérons que vous êtes satisfait de vos produits.
    
    N'hésitez pas à laisser un avis sur les produits que vous avez achetés :
    http://127.0.0.1:8000/boutique/
    
    À bientôt sur Grow With Green !
    
    L'équipe Grow With Green
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [commande.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur envoi email : {e}")
        return False