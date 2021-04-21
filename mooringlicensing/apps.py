from django.apps import AppConfig


class MooringlicensingConfig(AppConfig):
    name = 'mooringlicensing'

    def ready(self):
        import mooringlicensing.components.payments_ml.signals
