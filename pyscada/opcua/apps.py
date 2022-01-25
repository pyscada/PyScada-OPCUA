# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PyScadaOPCUAConfig(AppConfig):
    name = 'pyscada.opcua'
    verbose_name = _("PyScada OPC-UA")
    path = os.path.dirname(os.path.realpath(__file__))

    def ready(self):
        import pyscada.opcua.signals
