# -*- coding: utf-8 -*-

"""
Copyright (C) 2018, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.common.broker_message import CACHE
from zato.common.exception import BadRequest
from zato.common.odb.model import CacheMemcached
from zato.common.odb.query import cache_memcached_list
from zato.common.util import parse_extra_into_dict
from zato.server.service.internal import AdminService
from zato.server.service.internal.cache import common_instance_hook
from zato.server.service.meta import CreateEditMeta, DeleteMeta, GetListMeta

elem = 'cache_builtin'
model = CacheMemcached
label = 'a Memcached cache definition'
get_list_docs = 'Memcached cache definitions'
broker_message = CACHE
broker_message_prefix = 'MEMCACHED_'
list_func = cache_memcached_list
skip_input_params = ['cache_id']

# ################################################################################################################################

def response_hook(self, input, _ignored, attrs, service_type):

    if service_type == 'create_edit':
        self.response.payload.cache_id = self.response.payload.id

    elif service_type == 'get_list':
        for elem in self.response.payload:
            elem.id = elem.cache_id

# ################################################################################################################################

def instance_hook(self, input, instance, attrs):
    common_instance_hook(self, input, instance, attrs)

    if attrs.is_create_edit:

        # Parse extra arguments to confirm their syntax is correct,
        # output is ignored on purpose, we just want to validate it.
        parse_extra_into_dict(input.extra)

    elif attrs.is_delete:
        if instance.is_default:
            raise BadRequest(self.cid, 'Cannot delete the default cache')
        else:
            input.cache_type = instance.cache_type

# ################################################################################################################################

class GetList(AdminService):
    _filter_by = CacheMemcached.name,
    __metaclass__ = GetListMeta

# ################################################################################################################################

class Create(AdminService):
    __metaclass__ = CreateEditMeta

# ################################################################################################################################

class Edit(AdminService):
    __metaclass__ = CreateEditMeta

# ################################################################################################################################

class Delete(AdminService):
    __metaclass__ = DeleteMeta

# ################################################################################################################################
