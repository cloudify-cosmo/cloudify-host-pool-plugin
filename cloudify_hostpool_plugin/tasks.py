# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
'''
    tasks
    ~~~~~
    Handles host allocation and deallocation
'''

import os
import requests
import stat

from requests.exceptions import RequestException, Timeout

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation

from ._compat import httplib, urlparse, text_type

RUNTIME_PROPERTIES_KEYS = [
    'ip', 'user', 'port',
    'password', 'key', 'host_id'
]


@operation
def acquire(service_url, **_):
    '''Allocate a host for the user from the pool'''
    # Format the OS request
    requested_os = ctx.node.properties.get('os')
    if not isinstance(requested_os, text_type):
        raise NonRecoverableError('Requested OS must be a string')
    # Normalize filters
    filters = ctx.node.properties.get('filters', dict())
    filters['os'] = requested_os.lower()

    ctx.logger.info('Allocating host')
    ctx.logger.info('Calling POST "{0}", data="{1}"'.format(
        '{0}/host/allocate'.format(service_url), filters))
    try:
        response = requests.post(
            '{0}/host/allocate'.format(service_url), json=filters)
        ctx.logger.debug('Response received: {0}'.format(response.json()))
    except Timeout:
        # Catch ConnectTimeout & ReadTimeout errors
        raise RecoverableError('Timeout allocating host')
    except RequestException as exc:
        # Network error
        raise RecoverableError(
            'Network error allocating host: {0}'.format(exc))

    # Handle bad responses
    if response.status_code != httplib.OK:
        _handle_error(response)

    host = response.json()
    ctx.logger.info('Allocated host: {0}'.format(host))

    key_content = host.get('credentials', dict()).get('key')
    key_path = None
    svc_urlparse = urlparse(service_url)
    if key_content:
        key_path = _save_keyfile(
            key_content,
            '{0}_{1}_{2}'.format(
                svc_urlparse.hostname,
                svc_urlparse.port,
                host['id']))

    _set_runtime_properties(host, key_path)


@operation
def release(service_url, **_):
    '''Deallocate a host from the user to the pool'''
    ctx.logger.info('Deallocating host')
    host_id = ctx.instance.runtime_properties['host_id']
    try:
        response = requests.delete('{0}/host/{1}/deallocate'
                                   .format(service_url, host_id))
        ctx.logger.debug('Response received: {0}'.format(response))
    except Timeout:
        # Catch ConnectTimeout & ReadTimeout errors
        raise RecoverableError('Timeout deallocating host')
    except RequestException:
        # Catastrophic network error
        raise NonRecoverableError('Fatal network error deallocating host')

    # Handle bad responses
    if response.status_code != httplib.NO_CONTENT:
        _handle_error(response)

    key_file = ctx.instance.runtime_properties['key']
    if key_file and os.path.exists(key_file):
        os.unlink(key_file)

    _delete_runtime_properties()


def _save_keyfile(key_content, key_id):
    '''Write host SSH key to ~/.ssh'''
    key_path = os.path.expanduser('~/.ssh/key_{0}'.format(key_id))
    key_dir = os.path.dirname(key_path)
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)
    ctx.logger.debug('Saving key contents to {0}'.format(key_path))
    with open(key_path, 'w') as f_key:
        f_key.write(key_content)
    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
    return key_path


def _handle_error(response):
    '''Basic error handling'''
    try:
        reason = response.json().get('error', response.reason)
    except ValueError:
        reason = response.reason
    raise NonRecoverableError(
        'Error: {0}, Reason: {1}'.format(response.status_code, reason))


def _set_runtime_properties(host, key_path):
    '''Sets runtime properties for the acquired host'''
    ctx.instance.runtime_properties['host_id'] = host['id']
    ctx.instance.runtime_properties['os'] = host['os']
    ctx.instance.runtime_properties['ip'] = \
        host.get('endpoint', dict()).get('ip')
    ctx.instance.runtime_properties['port'] = \
        host.get('endpoint', dict()).get('port')
    ctx.instance.runtime_properties['user'] = \
        host.get('credentials', dict()).get('username')
    ctx.instance.runtime_properties['password'] = \
        host.get('credentials', dict()).get('password')
    ctx.instance.runtime_properties['key'] = key_path


def _delete_runtime_properties():
    '''Removes all runtime properties for the host'''
    for runtime_prop_key in RUNTIME_PROPERTIES_KEYS:
        if runtime_prop_key in ctx.instance.runtime_properties:
            del ctx.instance.runtime_properties[runtime_prop_key]
