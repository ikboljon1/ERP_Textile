from django.apps import AppConfig


class WmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wms'
    verbose_name = 'Управления складом'
    def ready(self):
        import wms.signals  # <-- Добавьте эту строку