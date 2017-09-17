# -*- coding: utf-8 -*-

'''
Interact with Redash.

https://redash.io
'''

import logging

# Define the module's virtual name
__virtualname__ = 'redash'

log = logging.getLogger(__name__)


def datasource_present(name, type, options):
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}
    update = False
    # Check if datasource exists
    datasources = __salt__['redash.list_datasources']()
    existing_ds = datasources.get(name)
    if existing_ds \
            and existing_ds['type'] == type \
            and existing_ds['options'] == options:
        # No changes in datasource
        # WARNING: this code path may be always dead as Redash seems to be 
        # censoring the returning password.
        ret['result'] = True
        ret['comment'] = 'The datasource "%s" is already present.' % name
        return ret
    else:
        update = True

    # Create the datasource if not present
    if not update:
        if (__salt__['redash.add_datasource'](name=name, type=type,
                                              options=options)):
            ret['result'] = True
            ret['comment'] = 'The datasource "%s" was created' % name
            # ret['changes'] = { name : { 'old': '', 'new': zone } }
    else:
        if (__salt__['redash.alter_datasource'](id=existing_ds['id'],
                                                name=name, type=type,
                                                options=options)):
            ret['result'] = True
            ret['comment'] = 'The datasource "%s" was updated' % name

    return ret
