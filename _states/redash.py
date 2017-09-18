# -*- coding: utf-8 -*-

'''
Interact with Redash.

https://redash.io
'''

import collections
import logging

# Define the module's virtual name
__virtualname__ = 'redash'

log = logging.getLogger(__name__)


def _compare_hashes(hash1, hash2, filter=[]):
    log.debug('Hash1: %s' % hash1)
    log.debug('Hash2: %s' % hash2)
    if len(hash1.keys()) != len(hash2.keys()):
        log.debug('Hashes have different number of keys')
        return False
    for key in hash1.keys():
        if key in filter:
            continue
        if key not in hash2.keys():
            log.debug('Key %s not found in hash2' % key)
            return False
        log.debug('Comparing key %s: %s - %s' % (key, hash1[key], hash2[key]))
        if hash1[key] != hash2[key]:
            return False
    log.debug('Hashes considered equal')
    return True

def datasource_present(name, type, options, force=False):
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    res = __salt__['redash.list_datasources'](name=name)
    # Check if datasource exists
    if name in res.keys():
        existing_ds = res[name]
        # Check whether the existing datasource is different
        # than the defintion
        log.debug('Datasource info for %s: %s' % (name, existing_ds))
        existing_options = existing_ds['options']
        if force or type != existing_ds['type'] \
                or not _compare_hashes(options, existing_options,
                                       filter=['password']):
            # Need to update the DS
            updated_ds = __salt__['redash.alter_datasource'](
                id=existing_ds['id'],
                name=name, type=type,
                options=options)
            ret['result'] = True
            ret['comment'] = 'Datasource was updated'
            ret['changes'] = {name: {'old': existing_ds, 'new': updated_ds}}
        else:
            ret['result'] = True
            ret['comment'] = 'Datasource is present'
    else:
        # Create the datasource if not present
        new_ds = __salt__['redash.add_datasource'](name=name, type=type,
                                                   options=options)
        if (new_ds):
            ret['result'] = True
            ret['comment'] = 'Datasource created'
            ret['changes'] = {name: {'old': '', 'new': new_ds}}

    return ret
