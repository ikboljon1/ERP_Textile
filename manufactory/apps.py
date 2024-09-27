from django.apps import AppConfig


class ManufactoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manufactory'
    verbose_name = 'Производства'
    def ready(self):
        import manufactory.signals