# #######
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
'''
    tasks
    ~~~~~
    Handles host allocation and deallocation
'''

import os
import requests
from requests.exceptions import RequestException, Timeout
import stat

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation

# pylint: disable=E1101
# Harmless warning due to the dynamically-generated LookupDict

RUNTIME_PROPERTIES_KEYS = [
    'ip', 'user', 'port',
    'password', 'key', 'host_id',
    'public_address'
]


@operation
def acquire(service_url, **_):
    '''Acquire a host for the user'''
    ctx.logger.info('Acquiring host')
    try:
        response = requests.post('{0}/hosts'.format(service_url))
        ctx.logger.debug('Response received: {0}'.format(response.text))
    except Timeout:
        # Catch ConnectTimeout & ReadTimeout errors
        raise RecoverableError('Timeout acquiring host')
    except RequestException:
        # Catastrophic network error
        raise NonRecoverableError('Fatal network error acquiring host')

    # Handle bad responses
    if response.status_code != requests.codes.CREATED:
        _handle_error(response)

    host = response.json()
    ctx.logger.info('Acquired host: {0}'.format(host['host']))

    key_content = host.get('auth', dict()).get('keyfile')
    key_path = None
    if key_content:
        key_path = _save_keyfile(key_content, host['host_id'])

    _set_runtime_properties(host, key_path)


@operation
def release(service_url, **_):
    '''Release a host from use by the user'''
    ctx.logger.info('Releasing host')
    host_id = ctx.instance.runtime_properties['host_id']
    try:
        response = requests.delete('{0}/hosts/{1}'
                                   .format(service_url, host_id))
        ctx.logger.debug('Response received: {0}'.format(response))
    except Timeout:
        # Catch ConnectTimeout & ReadTimeout errors
        raise RecoverableError('Timeout releasing host')
    except RequestException:
        # Catastrophic network error
        raise NonRecoverableError('Fatal network error releasing host')

    # Handle bad responses
    if not response.ok:
        _handle_error(response)

    key_file = ctx.instance.runtime_properties['key']
    if key_file and os.path.exists(key_file):
        os.unlink(key_file)

    _delete_runtime_properties()


def _save_keyfile(key_content, host_id):
    '''Write host SSH key to ~/.ssh'''
    key_path = os.path.expanduser('~/.ssh/key_{0}'.format(host_id))
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
    ctx.instance.runtime_properties['host_id'] = host.get('host_id')
    ctx.instance.runtime_properties['ip'] = host.get('host')
    ctx.instance.runtime_properties['port'] = host.get('port')
    ctx.instance.runtime_properties['user'] = \
        host.get('auth', dict()).get('username')
    ctx.instance.runtime_properties['password'] = \
        host.get('auth', dict()).get('password')
    ctx.instance.runtime_properties['key'] = key_path
    ctx.instance.runtime_properties['public_address'] = \
        host.get('public_address')


def _delete_runtime_properties():
    '''Removes all runtime properties for the host'''
    for runtime_prop_key in RUNTIME_PROPERTIES_KEYS:
        if runtime_prop_key in ctx.instance.runtime_properties:
            del ctx.instance.runtime_properties[runtime_prop_key]
