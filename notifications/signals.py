from django.db.models.signals import post_save
from django.dispatch import receiver
from commandes.models import Commande
from .models import Notification

@receiver(post_save, sender=Commande)
def creer_notification_commande(sender, instance, created, **kwargs):
    """Créer une notification automatique lors de la création d'une commande"""
    if created:
        Notification.creer_notification(
            user=instance.user,
            type='COMMANDE',
            titre=f'Commande #{instance.reference} confirmée',
            message=f'Votre commande d\'un montant de {instance.montant_total} FCFA a été enregistrée.',
            lien=f'/commandes/detail/{instance.pk}/'
        )