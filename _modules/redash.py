# -*- coding: utf-8 -*-
'''
Interact with Redash.

https://redash.io

'''

import json
import logging
import requests

from salt.exceptions import CommandExecutionError

__virtualname__ = 'redash'

log = logging.getLogger(__name__)


def _headers():
    api_key = __salt__['config.get']('redash:api_key')
    return {
        'Authorization': 'Key %s' % api_key,
        'Content-Type': 'application/json;charset=utf-8'
    }


def _url():
    return __salt__['config.get']('redash:api_url')


# GET a result and return its JSON
def _raw_get(path, params=None):
    url = '%s/%s' % (_url(), path)
    return requests.get(url, headers=_headers(), params=params).json()


def _get(path, id=None):
    if id:
        path = '%s/%s' % (path, id)
    result = _raw_get(path)
    # Processing pagination in response if necessary
    if isinstance(result, dict) and 'count' in result.keys():
        results = []
        current = 0
        count = result['count']
        page = 1
        while current < count:
            current = current + result['page_size']
            results.extend(result['results'])
            page = page + 1
            result = _raw_get(path, params={'page': page})
        result = results
    log.debug('Received from wire: %s' % result)
    return result


# POST a request and return its JSON
def _post(path, params=None, data=None):
    url = '%s/%s' % (_url(), path)
    res = requests.post(url, headers=_headers(), params=params,
                        data=json.dumps(data))
    content = res.json()

    if res.status_code != 200:
        raise CommandExecutionError('Server error when processing command: %s'
                                    % content['message'])

    return res.json()


# DELETE a request and return its JSON
def _delete(path, params=None):
    url = '%s/%s' % (_url(), path)
    res = requests.delete(url, headers=_headers(), params=params)
    log.debug('DELETE Status code: %s' % res.status_code)
    log.debug('DELETE Content: %s' % res.content)
    content = ''
    if res.status_code not in [200, 204]:
        content = res.json()
        raise CommandExecutionError('Server error when processing command: %s'
                                    % content['message'])
    return content


def _enhance_user(user):
    groups = []
    for group in user['groups']:
        log.debug('Fetching more info for group %d' % group)
        # Groups will always come as a hash with the group name as index
        for group in list_groups(id=group):
            groups.append(group)
    log.debug('Collected groups: %s' % groups)
    user['groups'] = groups
    email = user.pop('email')
    return email, user


def list_users(id=None, email=None):
    all_users = {}
    result = _get('users')
    if email:
        for user in result:
            if user['email'] == email:
                name, info = _enhance_user(user)
                all_users[name] = info
                break
        if not len(all_users.keys()):
            msg = 'Could not find user %s' % email
            log.error(msg)
            raise CommandExecutionError(msg)
    elif id:
        for user in result:
            if user['id'] == id:
                name, info = _enhance_user(user)
                all_users[name] = info
                break
        if not len(all_users.keys()):
            msg = 'Could not find user with id %d' % id
            log.error(msg)
            raise CommandExecutionError(msg)
    else:
        for user in result:
            name, info = _enhance_user(user)
            all_users[name] = info
    return all_users


def _enhance_ds(ds):
    log.debug('Enhancing datasource: %s' % ds)
    full_ds = _get('data_sources', id=ds['id'])
    ds_name = full_ds.pop('name')
    groups = []
    for group_id in full_ds['groups']:
        group = list_groups(id=group_id)
        if len(group):
            for group_name in group:
                groups.append(group_name)
    full_ds['groups'] = groups
    return ds_name, full_ds


def list_datasources(id=None, name=None):
    all_ds = {}
    if not name:
        log.debug('Searching datasource by id: %s' % id)
        data_sources = _get('data_sources', id=id)
        log.debug('Found datasources: %s' % data_sources)
        if type(data_sources) == list:
            log.debug('Received list of datasources')
            # Redash will send us a simplified list of each data source,
            # but we want to output a more detailed list indexed by name.
            for simple_ds in data_sources:
                name, full_ds = _enhance_ds(simple_ds)
                all_ds[name] = full_ds
        else:
            # Server couldn't find anything
            if 'message' in data_sources.keys():
                log.warning('Error message from server when searching'
                            ' for datasource %s: %s' %
                            (id, data_sources['message']))
            else:
                log.debug('Received single datasource')
                # Redash has returned us one single result,
                # let's enhance it anyway.
                name, full_ds = _enhance_ds(data_sources)
                all_ds[name] = full_ds
    else:
        log.debug('Searching datasource by name: %s' % name)
        # get all datasources
        data_sources = _get('data_sources')
        for ds in data_sources:
            if ds['name'] == name:
                name, full_ds = _enhance_ds(ds)
                all_ds[name] = full_ds
                break
    return all_ds


def add_datasource(name, type, options):
    ds = {
        'name': name,
        'type': type,
        'options': options
    }
    return _post('data_sources', data=ds)


def alter_datasource(id, name, type, options):
    ds = {
        'name': name,
        'type': type,
        'options': options
    }
    return _post('data_sources/%d' % id, data=ds)


def remove_datasource(id=None, name=None):
    ret = {
        'removed': []
    }
    if not name:
        res = list_datasources(id=id)
    else:
        res = list_datasources(name=name)
    # Popping the result
    for name, ds in res.items():
        log.debug('Datasource details retrieved for %s: %s' % (name, ds))
        if len(ds) > 0:
            _delete('data_sources/%d' % ds['id'])
            ret['removed'].append(ds)
        return ret


def _enhance_query(query):
    log.debug('Enhancing query: %s' % query)
    dsrcs = list_datasources(id=query.pop('data_source_id'))
    query['datasource'] = dsrcs.keys()[0]
    name = query.pop('name')
    return name, query


def list_queries(id=None, name=None):
    all_queries = {}
    if not name:
        log.debug('Searching queries by id: %s' % id)
        queries = _get('queries', id=id)
        # In case we go straight for an id we won't have a list.
        if type(queries) is not list:
            queries = [queries]
        # Ordering queries by name in the returning hash
        for query in queries:
            name, details = _enhance_query(query)
            all_queries[name] = details
    else:
        log.debug('Searching queries by name: %s' % name)
        queries = _get('queries')
        for query in queries:
            if query['name'] == name:
                name, details = _enhance_query(query)
                all_queries[name] = details
    return all_queries


def add_query(name, datasource, description, query, options={},
              schedule=None, publish=True):
    ret = {}
    queries = list_queries(name=name)
    if name in queries.keys():
        error = 'Query %s already exists' % name
        log.error(error)
        raise CommandExecutionError(error)

    datasource = list_datasources(name=datasource)[datasource]
    query = {
        'name': name,
        'data_source_id': datasource['id'],
        'description': description,
        'options': options,
        'query': query,
        'schedule': schedule
    }
    log.debug('Asking server to save query: %s' % query)
    new_query = _post('queries', data=query)
    # The following operations require a live query
    if publish or schedule:
        id = new_query['id']
        data = {}
        if publish:
            data['is_draft'] = False
        if schedule:
            data['schedule'] = schedule
        log.debug('Updating the query %d with extra parameters: %s'
                  % (id, data))
        # Refreshing information
        new_query = _post('queries/%d' % id, data=data)
        log.debug('Query published successfully')

    name, details = _enhance_query(new_query)
    ret[name] = details
    return ret


def alter_query(name, datasource, description, query, options={},
                schedule=None, publish=True):
    ret = {}
    queries = list_queries(name=name)
    if name not in queries.keys():
        error = 'Query %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)

    datasource = list_datasources(name=datasource)[datasource]
    query = {
        'name': name,
        'data_source_id': datasource['id'],
        'description': description,
        'options': options,
        'query': query,
        'schedule': schedule,
        'is_draft': not publish
    }
    log.debug('Asking server to save query: %s' % query)
    new_query = _post('queries/%d' % queries[name]['id'], data=query)

    name, details = _enhance_query(new_query)
    ret[name] = details
    return ret


def archive_query(name):
    ret = {"archived": {}}
    queries = list_queries(name=name)
    if name not in queries.keys():
        error = 'Query %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)
    _delete('queries/%d' % queries[name]['id'])
    ret['archived'][name] = queries[name]
    return ret


def _enhance_group(group):
    log.debug('Enhancing group: %s' % group)
    # Retrieving members list
    all_members = []
    for member in _get('groups/%d/members' % group['id']):
        all_members.append(member['email'])
    group['members'] = all_members
    # Retrieving datasources list
    all_ds = {}
    for ds in _get('groups/%d/data_sources' % group['id']):
        all_ds[ds['name']] = {
            'view_only': ds['view_only']
        }
    group['datasources'] = all_ds
    name = group.pop('name')
    return name, group


def list_groups(name=None, id=None):
    all_groups = {}
    if not name:
        log.debug('Searching groups by id: %s' % id)
        groups = _get('groups', id=id)
        # In case we go straight for an id we won't have a list.
        if type(groups) is not list:
            # We got a single result, let us verify that it isn't an error.
            # We need to do this because redash keeps memberships lingering in
            # the database after a group is removed.
            if 'message' in groups:
                log.info('No group found for id: %s' % groups)
                groups = []
            else:
                groups = [groups]
        # Ordering queries by name in the returning hash
        for group in groups:
            name, details = _enhance_group(group)
            all_groups[name] = details
    else:
        log.debug('Searching groups by name: %s' % name)
        groups = _get('groups')
        for group in groups:
            if group['name'] == name:
                name, details = _enhance_group(group)
                all_groups[name] = details
    return all_groups


def add_group(name, members=None):
    ret = {}
    groups = list_groups(name=name)
    if name in groups.keys():
        error = 'Group %s already exists' % name
        log.error(error)
        raise CommandExecutionError(error)
    group = {
        'name': name,
    }
    # Create new group
    new_group = _post('groups', data=group)
    name, details = _enhance_group(new_group)
    ret[name] = details
    return ret


def add_group_member(name, member):
    ret = {}
    groups = list_groups(name=name)
    if name not in groups.keys():
        error = 'Group %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)
    group = groups[name]
    # Need to re-add the name into the group info object
    group['name'] = name
    log.debug('Group info: %s' % group)
    if member in group['members']:
        log.warning('%s is already a member of group %s' % (member, name))
    else:
        log.debug('Adding user %s to group' % member)
        member_info = list_users(email=member)[member]
        log.debug('Found member info: %s' % member_info)
        payload = {'user_id': member_info['id']}
        _post('groups/%d/members' % group['id'], data=payload)
    name, details = _enhance_group(group)
    ret[name] = details
    return ret


def remove_group_member(name, member):
    ret = {}
    groups = list_groups(name=name)
    if name not in groups.keys():
        error = 'Group %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)
    group = groups[name]
    # Need to re-add the name into the group info object
    group['name'] = name
    log.debug('Group info: %s' % group)
    if member not in group['members']:
        log.warning('%s is already not a member of group %s' %
                    (member, name))
    else:
        member_info = list_users(email=member)[member]
        log.debug('Found member info: %s' % member_info)
        _delete('groups/%d/members/%d' % (group['id'], member_info['id']))
    name, details = _enhance_group(group)
    ret[name] = details
    return ret


def add_group_datasource(name, datasource):
    ret = {}
    groups = list_groups(name=name)
    if name not in groups.keys():
        error = 'Group %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)
    group = groups[name]
    group['name'] = name
    if datasource not in group['datasources'].keys():
        ds = list_datasources(name=datasource)[datasource]
        payload = {'data_source_id': ds['id']}
        _post('groups/%d/data_sources' % group['id'], data=payload)
    else:
        log.warning('Datasource %s already accessible to group' % datasource)
    name, details = _enhance_group(group)
    ret[name] = details
    return ret


def remove_group_datasource(name, datasource):
    ret = {}
    groups = list_groups(name=name)
    if name not in groups.keys():
        error = 'Group %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)
    group = groups[name]
    group['name'] = name
    if datasource in group['datasources'].keys():
        ds = list_datasources(name=datasource)[datasource]
        _delete('groups/%d/data_sources/%d' % (group['id'], ds['id']))
    else:
        log.warning('Datasource %s already not accessible to group' %
                    datasource)
    name, details = _enhance_group(group)
    ret[name] = details
    return ret


def alter_group_datasource(name, datasource, view_only=False):
    ret = {}
    groups = list_groups(name=name)
    if name not in groups.keys():
        error = 'Group %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)
    group = groups[name]
    group['name'] = name
    if datasource in group['datasources'].keys():
        current_view = group['datasources'][datasource].get('view_only', False)
        if current_view != view_only:
            log.warning('Changing datasource visibility')
            ds = list_datasources(name=datasource)[datasource]
            payload = {'view_only': view_only}
            _post('groups/%d/data_sources/%d' % (group['id'], ds['id']),
                  data=payload)
    else:
        raise CommandExecutionError('Datasource %s not accessible to group' %
                                    datasource)
    name, details = _enhance_group(group)
    ret[name] = details
    return ret


def delete_group(name):
    ret = {'deleted': {}}
    groups = list_groups(name=name)
    if name not in groups.keys():
        error = 'Group %s does not exist' % name
        log.error(error)
        raise CommandExecutionError(error)
    _delete('groups/%d' % groups[name]['id'])
    ret['deleted'][name] = groups[name]
    return ret


def list_dashboards(id=None):
    return _get('dashboards', id=id)


def list_alerts(id=None):
    return _get('alerts', id=id)
