########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

import os

from cosmo_tester.test_suites.test_blueprints import nodecellar_test
from cosmo_tester.framework import util

from system_tests import resources

REPO_URL = 'https://github.com/cloudify-cosmo/cloudify-host-pool-plugin.git'


os.environ['HANDLER_CONFIGURATION'] = '/home/elip/dev/system-tests-handlers/hp-openstack-region-b-dev2-handler.yaml'


class HostPoolPluginTest(nodecellar_test.NodecellarAppTest):

    def test_nodecellar_hostpool(self):
        self._provision_pool()
        self._install_host_pool_service()
        self._test_nodecellar_impl(
            'examples/nodecellar/host-pool-blueprint.yaml')

    def _provision_pool(self):

        blueprint_path = resources.get_resource(
            'pool-blueprint/pool-blueprint.yaml')
        self.blueprint_yaml = blueprint_path

        blueprint_id = '{0}-pool-blueprint'.format(self.test_id)
        deployment_id = '{0}-pool-deployment'.format(self.test_id)
        self.upload_deploy_and_execute_install(
            blueprint_id=blueprint_id,
            deployment_id=deployment_id,
            inputs={
                'image': self.env.ubuntu_image_id,
                'flavor': self.env.small_flavor_id
            }
        )
        self.pool_deployment_id = deployment_id

    def _install_host_pool_service(self):

        def _render_pool():

            hosts = self.client.deployments.outputs.get(
                deployment_id=self.pool_deployment_id).outputs['hosts']

            pool_template = resources.get_resource(
                'host-pool-service-blueprint/pool.yaml.template')
            util.render_template_to_file(
                template_path=pool_template,
                file_path=os.path.join(
                    os.path.dirname(pool_template),
                    'pool.yaml'),
                ip_pool_host_1=hosts['host_1']['ip'],
                ip_pool_host_2=hosts['host_2']['ip'],
                public_address_pool_host_1=hosts['host_1']['public_address'],
                public_address_pool_host_2=hosts['host_2']['public_address']
            )

        def _render_agent_key():

            with open(util.get_actual_keypath(
                    self.env,
                    self.env.agent_key_path)) as f:
                key_content = f.read()

            key_template = resources.get_resource(
                'host-pool-service-blueprint/keys/agent_key.pem.template')
            util.render_template_to_file(
                template_path=key_template,
                file_path=os.path.join(
                    os.path.dirname(key_template),
                    'agent_key.pem'),
                agent_private_key_file_content=key_content
            )

        _render_pool()
        _render_agent_key()

        blueprint_path = resources.get_resource(
            'host-pool-service-blueprint/openstack-host-'
            'pool-service-blueprint.yaml')
        self.blueprint_yaml = blueprint_path

        blueprint_id = '{0}-host-pool-service-blueprint'.format(self.test_id)
        deployment_id = '{0}-host-pool-service-deployment'.format(
            self.test_id)
        self.upload_deploy_and_execute_install(
            blueprint_id=blueprint_id,
            deployment_id=deployment_id,
            inputs={
                'image': self.env.ubuntu_image_id,
                'flavor': self.env.small_flavor_id
            }
        )
        self.host_pool_service_deployment_id = deployment_id

    @property
    def expected_nodes_count(self):
        return 5

    @property
    def host_expected_runtime_properties(self):
        return ['ip', 'user', 'port', 'host_id', 'public_address',
                'password', 'key']

    @property
    def entrypoint_node_name(self):
        return 'nodejs_host'

    @property
    def entrypoint_property_name(self):
        return 'public_address'

    @property
    def repo_url(self):
        return REPO_URL

    @property
    def repo_branch(self):
        return 'CFY-2209-system-tests'

    def get_inputs(self):

        # the host pool endpoint can be retrieved by getting the deployment
        # outputs of the host-pool-service deployment

        outputs = self.client.deployments.outputs.get(
            deployment_id=self.ho).outputs
        endpoint = 'http://{0}:{1}'.format(
            outputs['endpoint']['ip_address'],
            outputs['endpoint']['port'])
        return {'host_pool_service_endpoint': endpoint}

