from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def liste_notifications(request):
    notifications = Notification.objects.filter(user=request.user)
    non_lues = notifications.filter(lu=False).count()
    
    context = {
        'notifications': notifications,
        'non_lues': non_lues,
    }
    return render(request, 'notifications/liste.html', context)

@login_required
def marquer_lu(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.marquer_comme_lu()
    
    if notification.lien:
        return redirect(notification.lien)
    return redirect('notifications:liste')

@login_required
def tout_marquer_lu(request):
    Notification.objects.filter(user=request.user, lu=False).update(lu=True)
    return redirect('notifications:liste')