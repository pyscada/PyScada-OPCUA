# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pyscada

__version__ = '0.7.1rc1'
__author__ = 'Camille Lavayssière'

PROTOCOL_ID = 12

parent_process_list = [{'pk': PROTOCOL_ID,
                        'label': 'pyscada.opcua',
                        'process_class': 'pyscada.opcua.worker.Process',
                        'process_class_kwargs': '{"dt_set":30}',
                        'enabled': True}]
