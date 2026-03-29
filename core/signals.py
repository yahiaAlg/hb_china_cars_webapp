from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance, role="trader")  # default role


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, "userprofile"):
        instance.userprofile.save()


# ── Auth event logging ────────────────────────────────────────────────────────


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    from system_settings.models import SystemLog

    SystemLog.log(
        level="info",
        action_type="login",
        message=f"Connexion : {user.username}",
        user=user,
        request=request,
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    from system_settings.models import SystemLog

    if user:  # user is None if session was already expired
        SystemLog.log(
            level="info",
            action_type="logout",
            message=f"Déconnexion : {user.username}",
            user=user,
            request=request,
        )
