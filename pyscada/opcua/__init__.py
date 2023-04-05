# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = "0.8.0"
__author__ = "Camille Lavayssiere"
__email__ = "team@pyscada.org"
__description__ = "OPC-UA extension for PyScada a Python and Django based Open Source SCADA System"
__app_name__ = "OPCUA"

PROTOCOL_ID = 12

parent_process_list = [{'pk': PROTOCOL_ID,
                        'label': 'pyscada.opcua',
                        'process_class': 'pyscada.opcua.worker.Process',
                        'process_class_kwargs': '{"dt_set":30}',
                        'enabled': True}]
