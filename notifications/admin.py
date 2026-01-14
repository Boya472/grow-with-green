from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'titre', 'lu', 'date_creation']
    list_filter = ['type', 'lu', 'date_creation']
    search_fields = ['user__username', 'titre', 'message']
    readonly_fields = ['date_creation', 'date_lecture']
    
    actions = ['marquer_comme_lu']
    
    def marquer_comme_lu(self, request, queryset):
        for notif in queryset:
            notif.marquer_comme_lu()
        self.message_user(request, "Notifications marquées comme lues")
    marquer_comme_lu.short_description = "Marquer comme lu"
