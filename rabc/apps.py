from django.apps import AppConfig


class RabcConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rabc'

    def ready(self):
        import rabc.signals
