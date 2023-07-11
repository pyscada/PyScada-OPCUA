# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from . import __app_name__


class PyScadaOPCUAConfig(AppConfig):
    name = "pyscada." + __app_name__.lower()
    verbose_name = _("PyScada " + __app_name__)
    path = os.path.dirname(os.path.realpath(__file__))
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        __import__("pyscada." + __app_name__.lower() + ".signals")
