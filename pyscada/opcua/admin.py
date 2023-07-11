# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyscada.opcua import PROTOCOL_ID
from pyscada.opcua.models import OPCUADevice, ExtendedOPCUADevice
from pyscada.opcua.models import OPCUAVariable, ExtendedOPCUAVariable
from pyscada.opcua.models import OPCUAMethodArgument
from pyscada.admin import DeviceAdmin
from pyscada.admin import VariableAdmin
from pyscada.admin import admin_site
from pyscada.models import Device, DeviceProtocol, Variable
from django.contrib import admin
import nested_admin

import logging

logger = logging.getLogger(__name__)


class OPCUADeviceAdminInline(admin.StackedInline):
    model = OPCUADevice


class OPCUADeviceAdmin(DeviceAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "protocol":
            kwargs["queryset"] = DeviceProtocol.objects.filter(pk=PROTOCOL_ID)
            db_field.default = PROTOCOL_ID
        return super(OPCUADeviceAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    def get_queryset(self, request):
        """Limit Pages to those that belong to the request's user."""
        qs = super(OPCUADeviceAdmin, self).get_queryset(request)
        return qs.filter(protocol_id=PROTOCOL_ID)

    inlines = [OPCUADeviceAdminInline]


class OPCUAMethod(Variable):
    class Meta:
        proxy = True


class OPCUAMethodArgumentAdminNestedInline(nested_admin.NestedTabularInline):
    model = OPCUAMethodArgument
    sortable_field_name = "position"

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj else 1


class OPCUAMethodAdminInline(nested_admin.NestedTabularInline):
    model = OPCUAVariable
    sortable_field_name = "NamespaceIndex"
    inlines = [OPCUAMethodArgumentAdminNestedInline]
    verbose_name = "OPCUA Method"
    verbose_name_plural = "OPCUA Method"


class OPCUAMethodAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "unit",
        "value_class",
        "active",
        "writeable",
    )
    # list_editable = ('active', 'writeable',)
    list_display_links = ("name",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "device":
            kwargs["queryset"] = Device.objects.filter(protocol=PROTOCOL_ID)
        return super(OPCUAMethodAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "writeable":
            kwargs["initial"] = True
            # making the field readonly
            kwargs["disabled"] = True
        return super(OPCUAMethodAdmin, self).formfield_for_dbfield(
            db_field, request, **kwargs
        )

    def get_queryset(self, request):
        """Limit Pages to those that belong to the request's user."""
        qs = super(OPCUAMethodAdmin, self).get_queryset(request)
        return qs.filter(device__protocol_id=PROTOCOL_ID, writeable=True)

    inlines = [OPCUAMethodAdminInline]


class OPCUAMethodArgumentAdminInline(admin.TabularInline):
    model = OPCUAMethodArgument
    extra = 0


class OPCUAMethodAdmin2(admin.ModelAdmin):
    list_display = (
        "id",
        "opcua_variable",
        "NamespaceIndex",
        "Identifier",
    )
    list_editable = (
        "NamespaceIndex",
        "Identifier",
    )
    list_display_links = (
        "id",
        "opcua_variable",
    )
    # raw_id_fields = ('opcua_variable',)

    # Disable changing opcua_variable
    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.opcua_variable is not None:
            return ["opcua_variable"]
        return []

    def get_queryset(self, request):
        """Limit Pages to those that belong to the request's user."""
        qs = super(OPCUAMethodAdmin2, self).get_queryset(request)
        return qs.filter(opcua_variable__writeable=True)

    def has_add_permission(self, request):
        return False

    inlines = [OPCUAMethodArgumentAdminInline]


class OPCUAMethodArgumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "opcua_method",
        "position",
        "data_type",
        "value",
    )
    list_editable = (
        "opcua_method",
        "position",
        "data_type",
        "value",
    )
    list_display_links = ("id",)


# admin_site.register(ExtendedOPCUADevice, OPCUASeviceAdmin)
# admin_site.register(ExtendedOPCUAVariable, OPCUAVariableAdmin)
# admin_site.register(OPCUAMethod, OPCUAMethodAdmin)
admin_site.register(OPCUAMethod, OPCUAMethodAdmin)
# admin_site.register(OPCUAMethodArgument, OPCUAMethodArgumentAdmin)
