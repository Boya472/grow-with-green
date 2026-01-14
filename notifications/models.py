from django.db import models
from django.utils import timezone

class Notification(models.Model):
    """
    Système de notifications en temps réel
    """
    TYPE_CHOICES = (
        ('COMMANDE', 'Commande'),
        ('LIVRAISON', 'Livraison'),
        ('PROMO', 'Promotion'),
        ('ALERTE', 'Alerte'),
        ('INFO', 'Information'),
    )
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Utilisateur"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='INFO',
        verbose_name="Type"
    )
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    message = models.TextField(
        verbose_name="Message"
    )
    lien = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Lien",
        help_text="URL vers laquelle rediriger"
    )
    lu = models.BooleanField(
        default=False,
        verbose_name="Lu"
    )
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    date_lecture = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de lecture"
    )
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.user.username} - {self.titre}"
    
    def marquer_comme_lu(self):
        """Marque la notification comme lue"""
        if not self.lu:
            self.lu = True
            self.date_lecture = timezone.now()
            self.save()
    
    @staticmethod
    def creer_notification(user, type, titre, message, lien=None):
        """Méthode helper pour créer une notification"""
        return Notification.objects.create(
            user=user,
            type=type,
            titre=titre,
            message=message,
            lien=lien
        )
    
    @staticmethod
    def notifier_nouvelle_commande(commande):
        """Créer notification pour nouvelle commande"""
        Notification.creer_notification(
            user=commande.user,
            type='COMMANDE',
            titre=f"Commande {commande.numero_commande} confirmée",
            message=f"Votre commande d'un montant de {commande.montant_total} FCFA a été confirmée.",
            lien=f"/commandes/detail/{commande.numero_commande}/"
        )
    
    @staticmethod
    def notifier_expedition(commande):
        """Créer notification pour expédition"""
        Notification.creer_notification(
            user=commande.user,
            type='LIVRAISON',
            titre=f"Commande {commande.numero_commande} expédiée",
            message=f"Votre commande a été expédiée. Livraison estimée : {commande.zone_livraison.delai_livraison} jour(s).",
            lien=f"/commandes/detail/{commande.numero_commande}/"
        )
    
    @staticmethod
    def notifier_livraison(commande):
        """Créer notification pour livraison"""
        Notification.creer_notification(
            user=commande.user,
            type='LIVRAISON',
            titre="Commande livrée ! 🎉",
            message=f"Votre commande {commande.numero_commande} a été livrée. N'oubliez pas de laisser un avis !",
            lien=f"/commandes/detail/{commande.numero_commande}/"
        )