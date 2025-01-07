# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .. import PROTOCOL_ID
from pyscada.device import GenericHandlerDevice
from pyscada.models import DeviceProtocol, Variable
from pyscada.opcua.models import OPCUADevice

try:
    from asyncua import Client, Node, ua
    from asyncua.common.methods import uamethod, call_method_full
    from asyncua.common.ua_utils import *
    from concurrent.futures._base import TimeoutError

    try:
        from asyncio.exceptions import TimeoutError as asyncioTimeoutError
        from asyncio.exceptions import CancelledError
    except ModuleNotFoundError:
        # for python version < 3.8
        from asyncio import TimeoutError as asyncioTimeoutError
        from asyncio import CancelledError
    driver_ok = True
except ImportError:
    # asyncua = None
    driver_ok = False

from time import time

from asgiref.sync import async_to_sync

import logging

logger = logging.getLogger(__name__)


class GenericDevice(GenericHandlerDevice):
    def __init__(self, pyscada_device, variables):
        super().__init__(pyscada_device, variables)
        self._protocol = PROTOCOL_ID
        self.driver_ok = driver_ok
        self.is_connected = 0
        self.inst = None
        self.set_url()

    def set_url(self):
        self.url = "opc."
        self.url += str(
            self._device.opcuadevice.protocol_choices[
                self._device.opcuadevice.protocol
            ][1]
        )
        self.url += "://"
        self.url += str(self._device.opcuadevice.IP_address)
        self.url += ":"
        self.url += str(self._device.opcuadevice.port)
        self.url += str(self._device.opcuadevice.path)

    async def aconnect(self):
        """
        establish a connection to the Instrument
        """
        result = True
        if not self.connect():
            return False

        self.inst = Client(url=self.url, timeout=10)
        if self._device.opcuadevice.user is not None:
            self.inst.set_user(str(self._device.opcuadevice.user))
            if self._device.opcuadevice.password is not None:
                self.inst.set_password(str(self._device.opcuadevice.password))

        try:
            await self.inst.connect()
        except (TimeoutError, asyncioTimeoutError):
            result = False
            self._not_accessible_reason = f"Timeout connecting to {self._device}"
            await self.adisconnect()
        except CancelledError:
            result = False
            self._not_accessible_reason = (
                f"Cancelled while connecting to {self._device}"
            )
            await self.adisconnect()
        except OSError:
            result = False
            self._not_accessible_reason = f"Connect call to {self._device} failed"
            await self.adisconnect()

        if self._device_not_accessible > 0:
            tree = []
            # await self.browse_nodes(self.inst.nodes.objects, tree)
            # await self.browse_nodes(self.inst.nodes.types, tree)
            tree_str = ""
            for t in tree:
                if t["cls"] == "Method":
                    tree_str += (
                        str(t["name"])
                        + "("
                        + str(t["cls"])
                        + ") ns:"
                        + str(t["ns"])
                        + " i:"
                        + str(t["i"])
                        + "\n"
                    )
                elif t["type"] is not None:
                    tree_str += (
                        str(t["name"])
                        + "("
                        + str(t["type"])
                        + ") ns:"
                        + str(t["ns"])
                        + " i:"
                        + str(t["i"])
                        + "\n"
                    )
            self._device.opcuadevice.remote_devices_objects = str(tree_str)[
                : OPCUADevice._meta.get_field("remote_devices_objects").max_length
            ]
            # logger.debug(self._device.opcuadevice.remote_devices_objects)
            OPCUADevice.objects.abulk_update(
                [self._device.opcuadevice], ["remote_devices_objects"]
            )

        self.accessibility()

        return result

    async def adisconnect(self):
        result = False
        if self.inst is not None and hasattr(self.inst, "disconnect"):
            await self.inst.disconnect()
            result = True
        self.inst = None
        return result

    def read_data_all(self, variables_dict, erase_cache=False):
        return async_to_sync(self.aread_data_all)(variables_dict, erase_cache)

    async def aread_data_all(self, variables_dict, erase_cache=False):
        output = []

        if await self.abefore_read():
            for item in variables_dict.values():
                if item.readable:
                    value, read_time = await self.aread_data_and_time(item)
                    if (
                        value is not None
                        and read_time is not None
                        and item.update_values(
                            value, read_time, erase_cache=erase_cache
                        )
                    ):
                        output.append(item)
        await self.aafter_read()
        return output

    async def abefore_read(self):
        return await self.aconnect()

    async def aafter_read(self):
        """
        will be called after the last read_data
        """
        return await self.adisconnect()

    async def aread_data_and_time(self, variable_instance):
        """
        read values and timestamps from the device
        """

        return await self.aread_data(variable_instance), await self.atime()

    async def atime(self):
        return self.time()

    async def aread_data(self, variable):
        value = None
        try:
            node = self.inst.get_node(
                ua.NodeId(
                    variable.opcuavariable.Identifier,
                    variable.opcuavariable.NamespaceIndex,
                )
            )
            value = await node.read_value()
        except (TimeoutError, asyncioTimeoutError):
            logger.info(f"OPC-UA read value timeout for {self.ns_i}")
        except CancelledError:
            logger.info(f"OPC-UA read value cancelled for {self.ns_i}")
        except ua.uaerrors._auto.BadAttributeIdInvalid:
            # logger.debug('BadAttributeIdInvalid : %s' % variable)
            value = await self._call_method(variable)
        except Exception as e:
            logger.info(e)

        return value

    def write_data(self, variable_id, value, task):
        """
        write values to the device
        """
        return async_to_sync(self.awrite_data)(variable_id, value, task)

    async def awrite_data(self, variable_id, value, task):
        result = None

        variable = Variable.objects.get(id=variable_id)

        if await self.aconnect():
            result = await self._call_method(variable, value)
        await self.adisconnect()

        return result

    async def _call_method(self, variable, value=None):
        args = variable.opcuavariable.opcuamethodargument_set.all().order_by("position")
        result = None

        try:
            ns_i = ua.NodeId(
                variable.opcuavariable.Identifier, variable.opcuavariable.NamespaceIndex
            )
            node = self.inst.get_node(ns_i)
            inputs = await (await node.get_child("0:InputArguments")).read_value()
            if len(inputs) != len(args):
                logger.debug(
                    f"Bad method arguments quantity for : {variable}. Should be {len(inputs)} not {len(args)}."
                )
                return None
            args_values = []
            for i in range(0, len(inputs)):
                val = None
                if args[i].data_type == 0:
                    val = string_to_variant(
                        str(args[i].value),
                        await data_type_to_variant_type(
                            Node(node.server, inputs[i].DataType)
                        ),
                    )
                elif args[i].data_type == 1:
                    if value is None:
                        return None
                    try:
                        val = string_to_variant(
                            str(value),
                            self.value_class_to_variant_type(variable.value_class),
                        )
                    except ValueError:
                        val = string_to_variant(
                            str(int(value)),
                            self.value_class_to_variant_type(variable.value_class),
                        )
                if val is not None:
                    args_values.append(val)
            result = await call_method_full(await node.get_parent(), node, *args_values)
            if result.StatusCode.is_good():
                if hasattr(result, "OutputArguments") and len(result.OutputArguments):
                    result = result.OutputArguments[0]
                else:
                    result = value

        except (TimeoutError, asyncioTimeoutError):
            logger.info(f"OPC-UA read value timeout for {ns_i}")
        except CancelledError:
            logger.info(f"OPC-UA read value cancelled for {ns_i}")
        except ua.uaerrors._auto.BadAttributeIdInvalid:
            logger.info(f"BadAttributeIdInvalid : {variable}")
            pass
        except Exception as e:
            logger.info(e)
        return result

    async def browse_nodes(self, node: Node, tree):
        """
        Build a nested node tree dict by recursion (filtered by OPC UA objects and variables).
        """
        node_class = await node.read_node_class()
        for child in await node.get_children():
            # if await child.read_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable, ua.NodeClass.Method]:
            tree.append(await self.browse_nodes(child, tree))
        value = None
        if node_class != ua.NodeClass.Variable:
            var_type = None
        else:
            try:
                var_type = (await node.read_data_type_as_variant_type()).name
                value = await node.read_value()
            except ua.UaError:
                # logger.warning('Node Variable Type could not be determined for %r', node)
                var_type = None
        d = {
            "id": node.nodeid.to_string(),
            "ns": node.nodeid.NamespaceIndex,
            "i": node.nodeid.Identifier,
            "name": (await node.read_display_name()).Text,
            "cls": str(node_class.name),
            "type": var_type,
            "value": value,
        }
        return d

    def value_class_to_variant_type(self, class_str):
        VT = ua.VariantType
        if class_str.upper() in ["FLOAT64", "DOUBLE", "FLOAT", "LREAL", "UNIXTIMEF64"]:
            return VT.Float
        if class_str.upper() in ["FLOAT32", "SINGLE", "REAL", "UNIXTIMEF32"]:
            return VT.Float
        if class_str.upper() in ["UINT64"]:
            return VT.UInt64
        if class_str.upper() in ["INT64", "UNIXTIMEI64"]:
            return VT.Int64
        if class_str.upper() in ["INT32"]:
            return VT.Int32
        if class_str.upper() in ["UINT32", "DWORD", "UNIXTIMEI32"]:
            return VT.UInt32
        if class_str.upper() in ["INT16", "INT"]:
            return VT.Int16
        if class_str.upper() in ["UINT", "UINT16", "WORD"]:
            return VT.UInt16
        if class_str.upper() in ["INT8"]:
            return VT.SByte
        if class_str.upper() in ["UINT8", "BYTE"]:
            return VT.Byte
        if class_str.upper() in ["BOOL", "BOOLEAN"]:
            return VT.Boolean
        else:
            return VT.Variant
