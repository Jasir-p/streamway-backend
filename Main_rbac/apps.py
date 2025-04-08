from django.apps import AppConfig


class MainRbacConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Main_rbac'

    def ready(self):
        import Main_rbac.signals
