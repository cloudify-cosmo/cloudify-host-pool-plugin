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

import shutil
import os

from cosmo_tester.test_suites.test_blueprints import nodecellar_test
from cosmo_tester.framework import util

from system_tests import resources


class HostPoolPluginTest(nodecellar_test.NodecellarAppTest):

    def test_nodecellar_hostpool(self):
        self._provision_pool()
        self._install_host_pool_service()
        self._test_nodecellar_impl('host-pool-blueprint.yaml')
        self._teardown_pool()
        self._uninstall_host_pool_service()

    def assert_monitoring_data_exists(self):
        # this blueprint does not define monitoring
        pass

    def _provision_pool(self):

        self.password_pool_host = util.generate_password()

        def _render_password_authentication_script():

            script_template = resources.get_resource(
                'enable_password_authentication.sh.template')
            return util.render_template(
                template_path=script_template,
                password=self.password_pool_host)

        blueprint_path = resources.get_resource(
            'pool-blueprint/pool-blueprint.yaml')
        self.blueprint_yaml = blueprint_path

        blueprint_id = '{0}-pool-blueprint'.format(self.test_id)
        deployment_id = '{0}-pool-deployment'.format(self.test_id)

        script = _render_password_authentication_script()

        self.upload_deploy_and_execute_install(
            blueprint_id=blueprint_id,
            deployment_id=deployment_id,
            inputs={
                'image': self.env.ubuntu_trusty_image_id,
                'flavor': self.env.small_flavor_id,
                'enable_password_authentication_script': script
            }
        )
        self.pool_deployment_id = deployment_id

    def _teardown_pool(self):
        self.execute_uninstall(self.pool_deployment_id)

    def _install_host_pool_service(self):

        def _render_pool(_runtime_blueprint_directory):

            hosts = self.client.deployments.outputs.get(
                deployment_id=self.pool_deployment_id).outputs['hosts']

            pool_template = resources.get_resource(
                'host-pool-service-blueprint/pool.yaml.template')
            util.render_template_to_file(
                template_path=pool_template,
                file_path=os.path.join(
                    _runtime_blueprint_directory,
                    'pool.yaml'),
                ip_pool_host_1=hosts['host_1']['ip'],
                ip_pool_host_2=hosts['host_2']['ip'],
                public_address_pool_host_1=hosts['host_1']['public_address'],
                public_address_pool_host_2=hosts['host_2']['public_address'],
                password_pool_host=self.password_pool_host
            )

        def _render_agent_key(_runtime_blueprint_directory):

            with open(util.get_actual_keypath(
                    self.env,
                    self.env.agent_key_path)) as f:
                key_content = f.read()

            key_template = resources.get_resource(
                'host-pool-service-blueprint/keys/agent_key.pem.template')
            util.render_template_to_file(
                template_path=key_template,
                file_path=os.path.join(
                    _runtime_blueprint_directory,
                    'keys',
                    'agent_key.pem'),
                agent_private_key_file_content=key_content
            )

        # copy directory outside of source control since
        # we will be adding files to it.
        blueprint_directory = resources.get_resource(
            'host-pool-service-blueprint')
        runtime_blueprint_directory = os.path.join(
            self.workdir, 'host-pool-service-blueprint')
        shutil.copytree(src=blueprint_directory,
                        dst=runtime_blueprint_directory)

        _render_pool(runtime_blueprint_directory)
        _render_agent_key(runtime_blueprint_directory)

        self.blueprint_yaml = os.path.join(
            runtime_blueprint_directory,
            'openstack-host-pool-service-blueprint.yaml'
        )

        blueprint_id = '{0}-host-pool-service-blueprint'.format(self.test_id)
        deployment_id = '{0}-host-pool-service-deployment'.format(
            self.test_id)
        self.upload_deploy_and_execute_install(
            blueprint_id=blueprint_id,
            deployment_id=deployment_id,
            inputs={
                'image': self.env.ubuntu_trusty_image_id,
                'flavor': self.env.small_flavor_id
            }
        )

        self.host_pool_service_deployment_id = deployment_id

    def _uninstall_host_pool_service(self):
        self.execute_uninstall(self.host_pool_service_deployment_id)

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

    def get_inputs(self):

        # the host pool endpoint can be retrieved by getting the deployment
        # outputs of the host-pool-service deployment

        outputs = self.client.deployments.outputs.get(
            deployment_id=self.host_pool_service_deployment_id).outputs
        endpoint = 'http://{0}:{1}'.format(
            outputs['endpoint']['ip_address'],
            outputs['endpoint']['port'])
        return {'host_pool_service_endpoint': endpoint}
