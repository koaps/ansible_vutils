#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Koaps
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    from ansible.module_utils.virt_utils import VirtUtils
    VIRT_UTILS_FOUND = True
except ImportError:
    VIRT_UTILS_FOUND = False

class VUTILS_CMD:

    def __init__(self):

        if not VIRT_UTILS_FOUND:
            raise Exception("module utils virt_utils not found")

        self.check_mode = False
        self.cmd        = None
        self.data       = {}
        self.debug      = {}
        self.debug_on   = False
        self.reteval    = None
        self.retvar     = None
        self.result     = { 'changed': False, 'content': None, 'success': False }

    def _debug(self, **kwargs):
        if self.debug_on:
            if kwargs:
                self.debug.update(kwargs)
            else:
                return self.debug

    def _vutil_obj(self):
        vutils = VirtUtils(self.cmd, self.data, self.debug_on, self.reteval, self.retvar)
        vutils_obj = vutils.cmd_call()
        if vutils_obj is None:
            return {}
        return vutils_obj

    def _result(self):
        if self.debug_on:
            self.result['debug'] = self._debug()
        return self.result

    def _run_cmd(self, module, cmd):
        try:
            req_data      = module.params
            self.cmd      = cmd
            self.data     = req_data.pop('data', {})
            self.debug_on = req_data.pop('debug')

            self._debug(cmd=self.cmd)
            self._debug(data=self.data)
            self._debug(req_data=req_data)

            req_obj = self._vutil_obj()
            if req_obj is None:
                module.fail_json(msg='command not found: {}'.format(cmd))
                if maas.debug_on:
                    raise Exception("command not found")
        except Exception as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        try:
            self.result = req_obj()
            if self.result is None:
                module.fail_json(msg='command obj returned None')
        except Exception as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())
        return self.result

    def argspec(self):
        argument_spec=dict(
            debug = dict(type='bool', required=False, default=False),
        )
        return argument_spec

    def init(self, argument_spec):
        return AnsibleModule(argument_spec=argument_spec)

