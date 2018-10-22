#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Koaps
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import xml.etree.ElementTree as ET
    ET_FOUND = True
except ImportError:
    ET_FOUND = False

import collections
import json
import libvirt
import sys

class VirtUtils(object):

    def __init__(self, cmd, data, debug_on=False, reteval=None, retvar=None):
        #print("cmd: %s, data: %s, debug_on: %s, reteval: %s, retvar: %s" % (cmd, data, debug_on, reteval, retvar))
        if not ET_FOUND:
          raise Exception('ElementTree library is required for this module')
        """VirtUtils.

        :param cmd: The vutils command to run.
        :type cmd: ``str``
        :param debug_on: The turn on debug. The request and response are stored in debug key in JSON.
        :type debug_on: ``bool``
        :param data: The API request parameters.
        :type data: ``str``
        :param reteval: Evaluate this string against the response.
        :type reteval: ``str``
        :param retvar: Return just this key from the response.
        :type retvar: ``str``
        """
        if not cmd:
          raise Exception('missing required variable: cmd={}'.format(cmd))

        self.cmd        = cmd
        self.content    = {}
        self.conn       = None
        self.data       = data
        self.debug      = {}
        self.debug_on   = debug_on
        self.result     = { 'changed': False, 'content': None, 'success': False }
        self.reteval    = reteval
        self.retvar     = retvar

        self._conn_libvirt()

        if debug_on:
          self.result = { 'changed': False, 'content': None, 'debug': self.debug, 'success': False }

    def _conn_libvirt(self):
        try:
          self.conn = libvirt.open('qemu:///system')
          if self.conn == None:
            raise Exception('Failed to open connection to qemu:///system')
        except Exception as e:
          raise Exception( 'Failure: %s' % e)

    def _check_var(self, var_ar):
        if var_ar is None:
          raise Exception('check var failed: is None')
        if isinstance(var_ar,dict):
          for v in var_ar:
            if not v:
              raise Exception('check var failed: {}'.format(v))

    def _content(self):
        return self.content

    def _convert(self, data):
        if isinstance(data, basestring):
          return str(data)
        elif isinstance(data, collections.Mapping):
          return dict(map(self._convert, data.iteritems()))
        elif isinstance(data, collections.Iterable):
          return type(data)(map(self._convert, data))
        else:
          return data

    def _debug(self, **kwargs):
        if self.debug_on:
          if kwargs:
            self.debug.update(kwargs)
          else:
            return self.debug

    def _find_item(self, find_i, all_i):
        found_i = None
        if not isinstance(all_i, list):
          raise Exception('find_item err: not given list: {}'.format(all_i))
        for i in all_i:
          if isinstance(i, dict):
            if i.has_key(find_i):
              found_i = i
            if find_i in i.values()[0]:
              found_i = i
          else:
            if find_i == i:
              found_i = i
        self._check_var([found_i])
        return found_i

    def _parse_xml_macs(self, name, network, xml):
        macs = []
        if xml is None:
          return None
        tree = ET.fromstring(xml)
        for interface in tree.findall("devices/interface"):
          if interface.find("source").get("network") == network:
            macs.append(interface.find("mac").get("address"))
        return { name: macs }

    def _result(self):
        self.result['content'] = self._content()
        if self.debug_on:
          self.result['debug'] = self._debug()
        return self.result

    # used to get objects to make cmd calls
    def cmd_call(self):
        self._debug(cmd_call=self.cmd)
        return {
          'domain_create'  : self.domain_create,
          'domain_delete'  : self.domain_delete,
          'domain_find'    : self.domain_find,
          'domain_get'     : self.domain_get,
          'domain_state'   : self.domain_state,
          'storage_create' : self.storage_create,
          'storage_delete' : self.storage_delete,
          'storage_get'    : self.storage_get,
        }.get(self.cmd, self.cmd_error)

    def cmd_error(self, *args, **kwargs):
        self.content = 'cmd call error - unknown command'
        return self._result()

    def domain_create(self):
        xmlconfig = self.data['xmlconfig']
        self._check_var([xmlconfig])
        dom = self.conn.defineXML(xmlconfig)
        if not dom:
          return self._result()
        if dom is not None:
          dom.create()
          self.content = dom.name()
          self.result['success'] = True
        self.result['changed'] = True
        return self._result()

    def domain_delete(self):
        name = self.data['name']
        self._check_var([name])
        try:
          dom = self.conn.lookupByName(name)
          if not dom:
            return self._result()
          if dom is not None:
            if dom.isActive():
              dom.destroy()
            dom.undefine()
        except:
          pass
        self.result['success'] = True
        self.result['changed'] = True
        return self._result()

    def domain_find(self):
        mac = self.data['mac']
        network = self.data['network']
        self._check_var([mac, network])
        macs = map(lambda x: self._parse_xml_macs(x.name(), network, x.XMLDesc()), self.conn.listAllDomains())
        if not macs:
          return self._result()
        name = self._find_item(mac, macs)
        if name is not None:
          self.content = name.keys()[0]
          self.result['success'] = True
        self.result['changed'] = False
        return self._result()

    def domain_get(self):
        name    = self.data['name']
        network = self.data['network']
        self._check_var([name, network])
        try:
          dom = self.conn.lookupByName(name)
          if not dom:
            return self._result()
          if dom is not None:
            macs = map(lambda x: self._parse_xml_macs(x.name(), network, x.XMLDesc()), self.conn.listAllDomains())
            if not macs:
              return self._result()
            mac_t = self._find_item(name, macs)
            mac = self._convert(mac_t)[name][0]
            if not mac:
              return self._result()
            self.content = mac
        except:
          pass
        self.result['success'] = True
        self.result['changed'] = False
        return self._result()

    def domain_state(self):
        state_names = { libvirt.VIR_DOMAIN_RUNNING  : "running",
                        libvirt.VIR_DOMAIN_BLOCKED  : "blocked",
                        libvirt.VIR_DOMAIN_PAUSED   : "paused",
                        libvirt.VIR_DOMAIN_SHUTDOWN : "shutdown",
                        libvirt.VIR_DOMAIN_SHUTOFF  : "shutoff",
                        libvirt.VIR_DOMAIN_CRASHED  : "crashed",
                        libvirt.VIR_DOMAIN_NOSTATE  : "nostate" }
        name = self.data['name']
        self._check_var([name])
        try:
          dom = self.conn.lookupByName(name)
          if not dom:
            return self._result()
          if dom is not None:
            self.content = state_names[dom.info()[0]]
        except:
          pass
        self.result['success'] = True
        self.result['changed'] = False
        return self._result()

    def storage_create(self):
        pool      = self.data['pool']
        xmlconfig = self.data['xmlconfig']
        self._check_var([pool, xmlconfig])
        pool_obj  = self.conn.storagePoolLookupByName(pool)
        vol = pool_obj.createXML(xmlconfig, 0)
        if not vol:
          return self._result()
        if vol is not None:
          self.content = vol.key()
          self.result['success'] = True
        self.result['changed'] = True
        return self._result()

    def storage_delete(self):
        name = self.data['name']
        pool = self.data['pool']
        self._check_var([name, pool])
        pool_obj  = self.conn.storagePoolLookupByName(pool)
        vol  = pool_obj.storageVolLookupByName(name)
        if not vol:
          return self._result()
        if vol is not None:
          vol.delete()
        self.result['success'] = True
        self.result['changed'] = True
        return self._result()

    def storage_get(self):
        name = self.data['name']
        pool = self.data['pool']
        self._check_var([name, pool])
        vols = self.conn.storagePoolLookupByName(pool).listVolumes()
        if not vols:
          return self._result()
        vol = self._find_item(name, vols)
        if vol is not None:
          self.content = vol
        self.result['success'] = True
        self.result['changed'] = False
        return self._result()

