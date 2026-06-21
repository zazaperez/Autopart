from django.apps import AppConfig


class AppmotopartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'AppMotopart'

    def ready(self):
        import AppMotopart.signals  # noqa