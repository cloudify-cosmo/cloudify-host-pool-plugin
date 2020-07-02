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
import json
import pytest

from ecosystem_tests.dorkl import (
    blueprints_upload,
    deployments_create,
    executions_start,
    basic_blueprint_test,
    cleanup_on_failure,
    prepare_test,
    cloudify_exec
)
from __init__ import (
    PLUGINS_TO_UPLOAD,
    SECRETS_TO_CREATE
)


prepare_test(plugins=PLUGINS_TO_UPLOAD, secrets=SECRETS_TO_CREATE,
             execute_bundle_upload=False)

infra_blueprint = \
    'examples/service/examples/' \
    'blueprint-examples/virtual-machine/' \
    'openstack.yaml'
infra_test_name = 'infra-openstack'

service_test_name = 'service'
service_blueprint = 'examples/service/examples/blueprint.yaml'
service_inputs = 'infra_name=openstack'

plugin_test_name = 'hostpool'
plugin_blueprint = 'examples/blueprint.yaml'


@pytest.fixture(scope='function', params=[plugin_blueprint])
def blueprint_test(request):
    blueprints_upload(infra_blueprint,
                      infra_test_name)
    blueprints_upload(service_blueprint,
                      service_test_name)
    deployments_create(service_test_name, service_inputs)
    try:
        executions_start('install', service_test_name, 3000)
        capabilities = cloudify_exec(
            'cfy deployment outputs {0}'.format(service_test_name))
        try:
            basic_blueprint_test(request.param,
                                 plugin_test_name,
                                 inputs='service_url={0}'.format(
                                     capabilities['admin_url']['value']
                                 ))
        except:
            cleanup_on_failure(plugin_test_name)
            raise
        executions_start('uninstall', service_test_name, 3000)
    except:
        cleanup_on_failure(service_test_name)
        raise


def test_blueprint(blueprint_test):
    assert blueprint_test is None
