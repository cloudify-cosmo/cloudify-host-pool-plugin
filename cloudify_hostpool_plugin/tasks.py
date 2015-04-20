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

import os
import requests
import stat

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.decorators import operation


@operation
def acquire(service_url, **kwargs):
    ctx.logger.info('Acquire host')
    response = requests.post('{0}/hosts'.format(service_url))
    ctx.logger.debug('Response received: {0}'.format(response.text))
    if response.status_code == requests.codes.CREATED:
        host = response.json()
        ctx.logger.info('Acquired host: {0}'.format(host['host']))
        key_content = host['auth'].get('keyfile')
        key_path = None
        if key_content:
            key_path = _save_keyfile(key_content, host['host_id'])
        _set_runtime_properties(host, key_path)
    else:
        _handle_error(response)


@operation
def release(service_url, **kwargs):
    ctx.logger.info('Release host')
    host_id = ctx.instance.runtime_properties['host_id']
    response = requests.delete('{0}/hosts/{1}'.format(service_url, host_id))
    ctx.logger.debug('Response received: {0}'.format(str(response)))
    if not response.ok:
        _handle_error(response)
    key_file = ctx.instance.runtime_properties.get('key')
    if key_file and os.path.exists(key_file):
        os.unlink(key_file)


def _save_keyfile(key_content, host_id):
    key_path = os.path.expanduser('~/.ssh/key_{0}'.format(host_id))
    with open(key_path, 'w') as f:
        f.write(key_content)
    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
    return key_path


def _handle_error(response):
    try:
        reason = response.json().get('error', response.reason)
    except ValueError:
        reason = response.reason
    raise NonRecoverableError(
        'Error: {0} Reason: {1}'.format(response.status_code, reason))


def _set_runtime_properties(host, key_path):
    ctx.instance.runtime_properties['ip'] = host['host']
    ctx.instance.runtime_properties['user'] = host['auth']['username']
    ctx.instance.runtime_properties['port'] = host['port']
    ctx.instance.runtime_properties['host_id'] = host['host_id']
    ctx.instance.runtime_properties['public_address'] = host.get(
        'public_address')
    ctx.instance.runtime_properties['password'] = \
        host['auth'].get('password')
    ctx.instance.runtime_properties['key'] = key_path
