# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .. import PROTOCOL_ID
from pyscada.models import DeviceProtocol, Variable
from pyscada.opcua.models import OPCUADevice

try:
    from asyncua import Client, Node, ua
    from asyncua.common.methods import uamethod, call_method_full
    from asyncua.common.ua_utils import *
    from concurrent.futures._base import TimeoutError
    try:
        from asyncio.exceptions import TimeoutError as asyncioTimeoutError
    except ModuleNotFoundError:
        # for python version < 3.8
        from asyncio import TimeoutError as asyncioTimeoutError
    driver_ok = True
except ImportError:
    # asyncua = None
    driver_ok = False

from time import time

from asgiref.sync import async_to_sync

import logging

logger = logging.getLogger(__name__)


class GenericDevice:
    def __init__(self, pyscada_device, variables):
        self._device = pyscada_device
        self._variables = variables
        self.inst = None
        self.rm = None
        self.is_connected = 0

    def connect(self):
        return async_to_sync(self._connect)()

    async def _connect(self):
        """
        establish a connection to the Instrument
        """
        if not driver_ok:
            logger.error("Cannot import asyncua")
            return False

        if self._device.protocol.id != PROTOCOL_ID:
            logger.error("Wrong handler selected : it's for %s device while device protocol is %s" %
                         (str(DeviceProtocol.objects.get(id=PROTOCOL_ID)).upper(),
                          str(self._device.protocol).upper()))
            return False

        url = "opc."
        url += str(self._device.opcuadevice.protocol_choices[self._device.opcuadevice.protocol][1])
        url += "://"
        url += str(self._device.opcuadevice.IP_address)
        url += ":"
        url += str(self._device.opcuadevice.port)
        url += str(self._device.opcuadevice.path)

        self.inst = Client(url=url, timeout=10)
        self.inst.set_user(str(self._device.opcuadevice.user))
        self.inst.set_password(str(self._device.opcuadevice.password))

        try:
            await self.inst.connect()
            self.is_connected = 1
            logger.error("OPC-UA device : %s is now accessible" % str(self._device))
        except (TimeoutError, asyncioTimeoutError):
            if self.is_connected == 0:
                logger.warning("Timeout connecting to %s" % self._device)
        except OSError:
            if self.is_connected == 0:
                logger.warning("Connect call to %s failed" % self._device)

        #logger.debug(self.inst.__dict__)
        if self.is_connected > 0:
            tree = []
            await self.browse_nodes(self.inst.nodes.objects, tree)
            await self.browse_nodes(self.inst.nodes.types, tree)
            result = ''
            for t in tree:
                if t['cls'] == 'Method':
                    result += str(t['name']) + '(' + str(t['cls']) + ') ns:' + str(t['ns']) + ' i:' + str(t['i']) + '\n'
                elif t['type'] is not None:
                    result += str(t['name']) + '(' + str(t['type']) + ') ns:' + str(t['ns']) + ' i:' + str(t['i']) + '\n'
            self._device.opcuadevice.remote_devices_objects = \
                str(result)[:OPCUADevice._meta.get_field('remote_devices_objects').max_length]
            #logger.debug(self._device.opcuadevice.remote_devices_objects)
            OPCUADevice.objects.bulk_update([self._device.opcuadevice], ['remote_devices_objects'])

            #except Exception as e:
            #    logger.debug(e)
            #    return False

            #logger.debug('Connected to OPCUA device : %s' % self._device.opcuadevice.__str__())
            return True

        return False

    def disconnect(self):
        if self.inst is not None:
            async_to_sync(self._disconnect)()
            self.inst = None
            return True
        return False

    async def _disconnect(self):
        if self.is_connected > 0:
            await self.inst.disconnect()
            self.is_connected = 0

    def before_read(self):
        """
        will be called before the first read_data
        """
        return None

    def after_read(self):
        """
        will be called after the last read_data
        """
        return None

    def read_data(self, variable):
        return async_to_sync(self._read_data)(variable)

    async def _read_data(self, variable):
        if self.is_connected < 1:
            return None
        ns_i = "ns="
        ns_i += str(variable.opcuavariable.NamespaceIndex)
        ns_i += ";i="
        ns_i += str(variable.opcuavariable.Identifier)

        value = None
        try:
            value = await self.inst.get_node(ns_i).read_value()
        except (TimeoutError, asyncioTimeoutError):
            logger.info('OPC-UA read value timeout')
        except ua.uaerrors._auto.BadAttributeIdInvalid:
            #logger.debug('BadAttributeIdInvalid : %s' % variable)
            value = await self._call_method(variable, ns_i)
        except Exception as e:
            logger.info(e)
        return value

    def read_all_data(self, variables):
        return async_to_sync(self._read_all_data)(variables)

    async def _read_all_data(self, variables):
        await self._connect()

        if self.is_connected < 1:
            self.is_connected -= 1
        if self.is_connected == -1:  #
            logger.error("OPC-UA device : %s is not accessible" % str(self._device))

        output = []

        for variable in variables.values():
            if hasattr(self, 'inst') and self.inst is not None:
                value = await self._read_data(variable)
            else:
                value = None

            if value is not None and variable.update_value(value, time()):
                output.append(variable.create_recorded_data_element())

        await self._disconnect()
        return output

    def read_data_and_time(self, variable_instance):
        """
        read values and timestamps from the device
        """

        return self.read_data(variable_instance), self.time()

    def write_data(self, variable_id, value, task):
        """
        write values to the device
        """
        return async_to_sync(self._write_data)(variable_id, value, task)

        return False

    async def _write_data(self, variable_id, value, task):

        await self._connect()
        if self.is_connected < 1:
            return None

        variable = Variable.objects.get(id=variable_id)
        ns_i = "ns="
        ns_i += str(variable.opcuavariable.NamespaceIndex)
        ns_i += ";i="
        ns_i += str(variable.opcuavariable.Identifier)

        result = await self._call_method(variable, ns_i, value)
        await self._disconnect()
        return result

    async def _call_method(self, variable, ns_i, value=None):
        args = variable.opcuavariable.opcuamethodargument_set.all().order_by('position')
        result = None

        try:
            node = self.inst.get_node(ns_i)
            inputs = await (await node.get_child("0:InputArguments")).read_value()
            if len(inputs) != len(args):
                logger.debug("Bad method arguments quantity for : %s. Should be %s not %s."
                             % (variable, len(inputs), len(args)))
                return None
            args_values = []
            for i in range(0, len(inputs)):
                if args[i].data_type == 0:
                    val = string_to_variant(str(args[i].value),
                                            await data_type_to_variant_type(Node(node.server, inputs[i].DataType)))
                elif args[i].data_type == 1:
                    if value is None:
                        return None
                    try:
                        val = string_to_variant(str(value), self.value_class_to_variant_type(variable.value_class))
                    except ValueError:
                        val = string_to_variant(str(int(value)), self.value_class_to_variant_type(variable.value_class))
                args_values.append(val)
            result = await call_method_full(await node.get_parent(), node, *args_values)
            if result.StatusCode.is_good():
                if hasattr(result, 'OutputArguments') and len(result.OutputArguments):
                    result = result.OutputArguments[0]
                else:
                    result = value

        except (TimeoutError, asyncioTimeoutError):
            logger.info('OPC-UA read value timeout')
        except ua.uaerrors._auto.BadAttributeIdInvalid:
            logger.info('BadAttributeIdInvalid : %s' % variable)
            pass
        except Exception as e:
            logger.info(e)
        return result

    def time(self):
        return time()

    async def browse_nodes(self, node: Node, tree):
        """
        Build a nested node tree dict by recursion (filtered by OPC UA objects and variables).
        """
        node_class = await node.read_node_class()
        for child in await node.get_children():
            #if await child.read_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable, ua.NodeClass.Method]:
            tree.append(
                await self.browse_nodes(child, tree)
            )
        value = None
        if node_class != ua.NodeClass.Variable:
            var_type = None
        else:
            try:
                var_type = (await node.read_data_type_as_variant_type()).name
                value = await node.read_value()
            except ua.UaError:
                #logger.warning('Node Variable Type could not be determined for %r', node)
                var_type = None
        d = {
            'id': node.nodeid.to_string(),
            'ns': node.nodeid.NamespaceIndex,
            'i': node.nodeid.Identifier,
            'name': (await node.read_display_name()).Text,
            'cls': str(node_class.name),
            'type': var_type,
            'value': value,
        }
        return d

    def value_class_to_variant_type(self, class_str):
        VT = ua.VariantType
        if class_str.upper() in ['FLOAT64', 'DOUBLE', 'FLOAT', 'LREAL', 'UNIXTIMEF64']:
            return VT.Float
        if class_str.upper() in ['FLOAT32', 'SINGLE', 'REAL', 'UNIXTIMEF32']:
            return VT.Float
        if class_str.upper() in ['UINT64']:
            return VT.UInt64
        if class_str.upper() in ['INT64', 'UNIXTIMEI64']:
            return VT.Int64
        if class_str.upper() in ['INT32']:
            return VT.Int32
        if class_str.upper() in ['UINT32', 'DWORD', 'UNIXTIMEI32']:
            return VT.UInt32
        if class_str.upper() in ['INT16', 'INT']:
            return VT.Int16
        if class_str.upper() in ['UINT', 'UINT16', 'WORD']:
            return VT.UInt16
        if class_str.upper() in ['INT8']:
            return VT.SByte
        if class_str.upper() in ['UINT8', 'BYTE']:
            return VT.Byte
        if class_str.upper() in ['BOOL', 'BOOLEAN']:
            return VT.Boolean
        else:
            return VT.Variant
