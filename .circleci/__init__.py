########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os

OS_VERSION = '3.2.16'
OS_WAGON = 'https://github.com/cloudify-cosmo/cloudify-openstack-plugin/' \
           'releases/download/{v}/cloudify_openstack_plugin-{v}-' \
           'centos-Core-py27.py36-none-linux_x86_64.wgn'.format(v=OS_VERSION)
OS_PLUGIN = 'https://github.com/cloudify-cosmo/cloudify-openstack-plugin/' \
            'releases/download/{v}/plugin.yaml'.format(v=OS_VERSION)

PLUGINS_TO_UPLOAD = [(OS_WAGON, OS_PLUGIN)]


SECRETS_TO_CREATE = {
    'openstack_username': False,
    'openstack_password': False,
    'openstack_tenant_name': False,
    'openstack_auth_url': False,
    'openstack_region': False,
    'openstack_region_name': False,
    'openstack_external_network': False,
    'openstack_project_id': False,
    'openstack_project_name': False,
    'openstack_project_domain_id': False,
    'openstack_user_domain_name': False,
    'openstack_project_domain_name': False,
    'base_image_id': False,
    'base_flavor_id': False,
}

