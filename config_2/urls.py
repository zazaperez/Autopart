from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from AppMotopart.views import (
    password_reset_complete_view,
    password_reset_confirm_view,
    password_reset_done_view,
    password_reset_request,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('AppMotopart.urls')),

    # Recuperación de contraseña
    path('password-reset/', password_reset_request, name='password_reset'),
    path('password-reset/done/', password_reset_done_view, name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset/complete/', password_reset_complete_view, name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)