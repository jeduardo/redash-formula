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
    content = json.dumps('')
    if res.headers['Content-Length'] > 0:
        content = res.json()

    if res.status_code != 204:
        raise CommandExecutionError('Server error when processing command: %s'
                                    % content['message'])

    return content


def list_queries(id=None):
    return _get('queries', id=id)


def list_users(id=None):
    return _get('users', id=id)


def list_datasources(id=None):
    all_ds = {}
    data_sources = _get('data_sources', id=id)
    # Redash will send us a simplified list of each data source, but we want to
    # output a more detailed list indexed by name.
    for simple_ds in data_sources:
        full_ds = _get('data_sources', id=simple_ds['id'])
        ds_name = full_ds.pop('name')
        all_ds[ds_name] = full_ds
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


def remove_datasource(id):
    return _delete('data_sources/%d' % id)


def list_dashboards(id=None):
    return _get('dashboards', id=id)


def list_alerts(id=None):
    return _get('alerts', id=id)
