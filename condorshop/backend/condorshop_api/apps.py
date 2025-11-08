import logging
import os

from django.apps import AppConfig
from django.conf import settings
from django.contrib import admin
from django.db import OperationalError, ProgrammingError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

_sessions_flushed = False
_admin_login_wrapped = False


class CondorShopAPIConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'condorshop_api'

    def ready(self):
        if not settings.DEBUG:
            return

        self._wrap_admin_login()
        self._flush_sessions_on_start()

    def _wrap_admin_login(self):
        global _admin_login_wrapped
        if _admin_login_wrapped:
            return

        original_login = admin.site.__class__.login

        decorated_login = method_decorator(never_cache)(original_login)
        decorated_login = method_decorator(
            ratelimit(key='ip', rate='5/m', method='POST', block=True)
        )(decorated_login)

        admin.site.__class__.login = decorated_login
        _admin_login_wrapped = True
        logger.info("Rate limiting habilitado para /admin/login/ en entorno de desarrollo.")

    def _flush_sessions_on_start(self):
        global _sessions_flushed
        if _sessions_flushed:
            return

        run_main = os.environ.get('RUN_MAIN')
        if run_main != 'true':
            # Evitar ejecutar en el proceso padre del autoreloader
            return

        from django.contrib.sessions.models import Session

        try:
            deleted, _ = Session.objects.all().delete()
            logger.info("Sesiones de desarrollo invalidadas al iniciar runserver (total eliminadas: %s).", deleted)
        except (OperationalError, ProgrammingError) as exc:
            logger.warning("No se pudieron invalidar sesiones al iniciar runserver: %s", exc)

        _sessions_flushed = True

