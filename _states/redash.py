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


def datasource_absent(name):
    ret = {'name': name,
       'changes': {},
       'result': False,
       'comment': ''}
    # Check if datasource_absent is present
    res = __salt__['redash.list_datasources'](name=name)
    if name in res.keys():
        old_datasource = res[name]
        __salt__['redash.remove_datasource'](name=name)
        ret['result'] = True
        ret['comment'] = 'Datasource was removed'
        ret['changes'] = {
            'old': {
                name: old_datasource
            },
            'new': {
                name: None
            }
        }
    else:
        ret['result'] = True
        ret['comment'] = 'Datasource is absent'
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


def user_present(email, name):
    ret = {'name': email,
           'changes': {},
           'result': False,
           'comment': ''}
    res = __salt__['redash.list_users'](email=email)
    log.debug('Result received from module: %s' % res)
    # Check if the user is already there
    if email in res.keys():
        # Are the variable properties as they should be?
        user = res[email]
        log.debug('Current user properties: %s' % user)
        if user['name'] == name:
            ret['result'] = True
            ret['comment'] = 'User is present'
        else:
            # If the user exists, then update the required attributes
            res = __salt__['redash.alter_user'](email=email, name=name)
            if res:
                ret['result'] = True
                ret['comment'] = 'User was updated'
                ret['changes'] = {
                    'old': {
                        email: user
                    },
                    'new': {
                        email: res[email]
                    }
                }
    else:
        # We have no user here, let's create it.
        res = __salt__['redash.add_user'](email=email, name=name)
        if res:
            ret['result'] = True
            ret['comment'] = 'User was created'
            ret['changes'] = {
                'old': {
                    email: 'Not present'
                },
                'new': {
                    email: res[email]
                }
            }
    # Return the result
    return ret


def group_present(name, members=[], datasources={}):
    ret = {'name': name,
       'changes': {},
       'result': False,
       'comment': ''}
    changes = False
    # Check if group is present. 
    res = __salt__['redash.list_groups'](name=name)
    if name in res.keys():
        old_group = res[name]
        cur_group = res[name]
    else:
        old_group = None
        cur_group = None
    # If not present, then create it.
    if not cur_group:
        res = __salt__['redash.add_group'](name=name)
        cur_group = res[name]

    # Now we have a group. Let's check if we need to change the members list.
    members_add = []
    members_remove = []
    for member in members:
        if member not in cur_group['members']:
            members_add.append(member)
    for member in cur_group['members']:
        if member not in members:
            members_remove.append(member)
    log.debug('Members to add: %s' % members_add)
    log.debug('Members to remove: %s' % members_remove)
    for member in members_add:
        __salt__['redash.add_group_member'](name=name, member=member)
        changes = True
    for member in members_remove:
        __salt__['redash.remove_group_member'](name=name, member=member)
        changes = True

    # Similar procedure for the datasources.
    ds_add = []
    ds_remove = []
    for ds in datasources:
        if ds not in cur_group['datasources']:
            ds_add.append(ds)
    for ds in cur_group['datasources']:
        if ds not in datasources:
            ds_remove.append(member)
    log.debug('Datasources to add: %s' % ds_add)
    log.debug('Datasources to remove: %s' % ds_remove)
    for ds in ds_add:
        __salt__['redash.add_group_datasource'](name=name, datasource=ds)
        changes = True
    for ds in ds_remove:
        __salt__['redash.remove_group_datasource'](name=name, datasource=ds)
        changes = True

    # Now we get the current view of the new group
    cur_group = __salt__['redash.list_groups'](name=name)

    # Fill in the old and new values and it should be all done.
    if not old_group:
        ret['comment'] = 'Group was created'
    elif changes:
        ret['comment'] = 'Group was updated'
        ret['changes'] = {
            'old': {
                name: old_group
            },
            'new': {
                name: cur_group
            }
        }
    else:
        ret['comment'] = 'Group is present and in the desired state'
    ret['result'] = True
    return ret


def group_absent(name):
    ret = {'name': name,
       'changes': {},
       'result': False,
       'comment': ''}
    # Check if group is present
    res = __salt__['redash.list_groups'](name=name)
    if name in res.keys():
        old_group = res[name]
        __salt__['redash.remove_group'](name=name)
        ret['result'] = True
        ret['comment'] = 'Group was removed'
        ret['changes'] = {
            'old': {
                name: old_group
            },
            'new': {
                name: None
            }
        }
    else:
        ret['result'] = True
        ret['comment'] = 'Group is absent'
    return ret
