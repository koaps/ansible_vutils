#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Koaps
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'curated'
}

DOCUMENTATION = '''
---
module: vutils_storage_delete
short_description: delete storage vol
extends_documentation_fragment: vutils
description:
    - "This module is for virt utils"
version_added: "2.4"

options:
    debug:
        default: false
        description:
            - Turn on module debugging output
        required: false
        type: bool
    pool:
        default: zfspool
        description:
            - Pool name for storage vol
        required: false
    name:
        description:
            - Name of storage vol to delete
        required: true

author:
    - Koaps
'''

EXAMPLES = '''
- name: delete storage vol
  vutils_storage_delete:
    pool : "{{ pool }}"
    name : "{{ name }}"
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
content:
    description: The output returned from the MAAS command
    returned: success
    sample: [ { "name": "local" } ]
    type: list
    sample: ['...', '...']
success:
    description: A flag indicating if API call was a success or not
    returned: success
    type: boolean
    sample: True
'''

import json
from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.modules.cloud.misc.vutils.library.vutils_cmd import VUTILS_CMD
    VUTILS = True
except ImportError:
    VUTILS = False

_debug = {}
def debug(*args, **kwargs):
    if kwargs:
        _debug.update(kwargs)
    else:
        return _debug

def main():
    if not VUTILS:
        raise Exception("virt_utils library not found")
    vutils_cmd = VUTILS_CMD()
    argspec = vutils_cmd.argspec()
    if argspec is None:
        raise Exception("argspec returned None")

    argspec['pool'] = dict(required=False, type='str', default='zfspool')
    argspec['name'] = dict(required=True, type='str')

    module = vutils_cmd.init(argspec)
    data = dict(
        pool = module.params.pop('pool', None),
        name = module.params.pop('name', None),
    )
    module.params['data'] = data
    debug(params=module.params.copy())

    result = vutils_cmd._run_cmd(module, 'storage_delete')

    if vutils_cmd.debug_on:
        try:
            debug(result=json.dumps(result))
        except (TypeError, ValueError):
            debug(result=result)
    else:
        if result['success']:
            module.exit_json(**result)
        else:
            module.fail_json(msg=result['content'])

if __name__ == '__main__':
    main()
    print(_debug['result'])
