# -*- coding: utf-8 -*-

# Copyright (c) 2023, Steffen Scheib <steffen@scheib.me>
# GNU General Public License v3.0+
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
WARNING:
This filter plugin is not intended to be used outside of this roles context.
The filter has only been tested with a specific data type: lists of dictionaries.
If you pass anything else to the filter, it will error out!
'''

__metaclass__ = type

import yaml
from ansible.errors import AnsibleFilterError
from ansible.module_utils.common.text.converters import to_native, to_text

class IncreaseIndentDumper(yaml.Dumper):
    '''Custom Dumper to indent lists by two spaces'''

    def increase_indent(self, flow=False, indentless=False):
        return super(IncreaseIndentDumper, self).increase_indent(flow, False)

def list_of_dicts_to_indented_yaml(obj, indent=2, top_key=None, **kwargs):
    '''Convert a list of dictionaries to a YAML formatted string'''

    if not isinstance(obj, list):
        raise AnsibleFilterError(f'to_very_nice_yaml: Provided data is not a list, it is {type(i)}')

    data = list()
    for i in obj:

        if not isinstance(i, dict):
            raise AnsibleFilterError(f'to_very_nice_yaml: List entry is not a dictionary, it is {type(i)}.'
                                     f'value: {i}')

        # get keys of the dict
        keys = list(i.keys())

        if top_key:
            # check if top_key is in the keys
            if top_key not in keys:
                raise AnsibleFilterError(f'to_very_nice_yaml: key {top_key} not in list {i}')

            # remove top_key
            keys.remove(top_key)

            # insert top_key at index 0
            keys.insert(0, top_key)

        # sort the dict by index and append it to data
        data.append(dict(sorted(i.items(), key=lambda x: keys.index(x[0]))))

    try:
        transformed = yaml.dump(data, Dumper=IncreaseIndentDumper, indent=indent, allow_unicode=True, default_flow_style=False, **kwargs)
    except Exception as e:
        raise AnsibleFilterError(f'to_very_nice_yaml: {to_native(e)}', orig_exc=e)
    return to_text(transformed)


class FilterModule(object):
    ''' Query filter '''

    def filters(self):

        return {
            'list_of_dicts_to_indented_yaml': list_of_dicts_to_indented_yaml
        }
