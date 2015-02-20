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
import httplib
import os
import requests

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.decorators import operation


@operation
def acquire(service_url, **kwargs):
    ctx.logger.info("Acquire host")
    response = requests.post('{0}/hosts'.format(service_url))
    host = response.json()
    ctx.logger.info("Response received: {0}".format(str(host)))
    if response.status_code == httplib.CREATED:
        ctx.instance.runtime_properties['ip'] = host['host']
        key_path = _save_keyfile(host['auth']['keyfile'], host['host_id'])
        agent = {'user': host['auth']['username'],
                 'key': key_path}
        ctx.instance.runtime_properties['cloudify_agent'] = agent
        ctx.instance.runtime_properties['host'] = host
    else:
        raise NonRecoverableError(response.json())


@operation
def release(service_url, **kwargs):
    ctx.logger.info("Release host")
    host_id = ctx.instance.runtime_properties['host']['host_id']
    response = requests.delete('{0}/hosts/{1}'.format(service_url, host_id))
    ctx.logger.info("Response received: {0}".format(str(response)))
    if not response.ok:
        ctx.logger.warning(response.text)
    key_file = ctx.instance.runtime_properties['cloudify_agent'].get('key')
    if key_file and os.path.exists(key_file):
        os.unlink(key_file)


def _save_keyfile(key_content, host_id):
    ctx.logger.info("Save key")
    key_path = "~/.ssh/key_{0}".format(host_id)
    key_path = os.path.expanduser(key_path)
    with open(key_path, 'w') as f:
        f.write(key_content)
    return key_path
