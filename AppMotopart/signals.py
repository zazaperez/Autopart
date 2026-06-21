from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Carrito, Perfil


@receiver(post_save, sender=User)
def crear_perfil_y_carrito(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)
        Carrito.objects.create(usuario=instance)
    else:
        Perfil.objects.get_or_create(usuario=instance)
        Carrito.objects.get_or_create(usuario=instance)