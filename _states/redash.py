# -*- coding: utf-8 -*-

'''
Interact with Redash.

https://redash.io
'''

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
            ret['changes'] = {
                'old': {
                    name: existing_ds
                },
                'new': {
                    name: updated_ds
                }
            }
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
            ret['changes'] = {
                'old': {
                    name: 'Not present'
                },
                'new': {
                    name: updated_ds
                }
            }

    return ret


def query_present(name, datasource, description, query, options={},
                  schedule=None, publish=True):
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    res = __salt__['redash.list_queries'](name=name)
    # Check if query exists
    if name in res.keys():
        existing_query = res[name]
        # Check whether the existing query is different
        # than the defintion
        log.debug('Query info for %s: %s' % (name, existing_query))
        if existing_query['datasource'] != datasource \
                or existing_query['description'] != description \
                or existing_query['query'] != query \
                or str(existing_query['schedule']) != str(schedule) \
                or existing_query['is_draft'] != (not publish) \
                or not _compare_hashes(existing_query['options'], options):
            # Need to update the query

            res = __salt__['redash.alter_query'](
                name=name,
                datasource=datasource,
                description=description,
                query=query,
                options=options,
                schedule=schedule,
                publish=publish)
            ret['result'] = True
            ret['comment'] = 'Query was updated'
            ret['changes'] = {
                'old': {
                    name: existing_query
                },
                'new': {
                    name: res[name]
                }
            }
        else:
            ret['result'] = True
            ret['comment'] = 'Query is present'
    else:
        # Create the query if not present
        res = __salt__['redash.add_query'](
            name=name,
            datasource=datasource,
            description=description,
            query=query,
            options=options,
            schedule=schedule,
            publish=publish)
        ret['result'] = True
        ret['comment'] = 'Datasource created'
        ret['changes'] = {
            'old': {
                name: 'Not present'
            },
            'new': {
                name: res[name]
            }
        }

    return ret
