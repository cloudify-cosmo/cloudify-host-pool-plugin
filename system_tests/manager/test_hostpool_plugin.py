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

import requests
import uuid

from cosmo_tester.test_suites.test_blueprints import nodecellar_test
from cosmo_tester.framework.git_helper import clone
from cosmo_tester.framework.test_cases import MonitoringTestCase
from cosmo_tester.framework.cfy_helper import DEFAULT_EXECUTE_TIMEOUT

from system_tests import resources

UBUNTU_HOST = 'ubuntu_host_template'
CENTOS_HOST = 'centos_host_template'
WINDOWS_HOST = 'windows_host_template'
HOST_TEMPLATES = [WINDOWS_HOST, CENTOS_HOST, UBUNTU_HOST]
EXTENDED_TIMEOUT = 3600 # default is 1800. These windows VMs take forever.

class HostPoolPluginTest(nodecellar_test.NodecellarAppTest):

    def test_nodecellar_hostpool(self):
        self._install_service_with_seed_vms()
        self.addCleanup(self._uninstall_host_pool_service)
        hosts = self._get_hosts(self.host_pool_service_deployment_id)
        self.assertEquals(len(hosts), len(HOST_TEMPLATES))
        for host in hosts:
            self._assert_host_state(host)
        self._scale(UBUNTU_HOST)
        hosts = self._get_hosts(self.host_pool_service_deployment_id)
        self.assertEquals(len(hosts), len(HOST_TEMPLATES) + 1)
        self._test_nodecellar_impl('host-pool-blueprint.yaml')
        hosts = self._get_hosts(self.host_pool_service_deployment_id)
        self.assertEquals(len(hosts), len(HOST_TEMPLATES) + 1)
        for host in hosts:
            self._assert_host_state(host)


    def _test_nodecellar_impl(
        self, blueprint_file, execute_timeout=DEFAULT_EXECUTE_TIMEOUT
        ):

        self.repo_dir = clone(self.repo_url, self.workdir)
        self.blueprint_yaml = self.repo_dir / blueprint_file

        self.modify_blueprint()

        before, after = self.upload_deploy_and_execute_install(
            inputs=self.get_inputs(),
            execute_timeout=execute_timeout
        )

        self.post_install_assertions(before, after)

        self.execute_uninstall()

        self.post_uninstall_assertions()

    def post_install_assertions(self, before_state, after_state):

        delta = self.get_manager_state_delta(before_state, after_state)

        self.logger.info('Current manager state: {0}'.format(delta))

        self.assertEqual(len(delta['blueprints']), 1,
                         'blueprint: {0}'.format(delta))

        self.assertEqual(len(delta['deployments']), 1,
                         'deployment: {0}'.format(delta))

        deployment_from_list = delta['deployments'].values()[0]

        deployment_by_id = self.client.deployments.get(deployment_from_list.id)
        self.deployment_id = deployment_from_list.id

        executions = self.client.executions.list(
            deployment_id=deployment_by_id.id)

        self.assertEqual(len(executions), 2,
                         'There should be 2 executions but are: {0}'.format(
                             executions))

        execution_from_list = executions[0]
        execution_by_id = self.client.executions.get(execution_from_list.id)

        self.assertEqual(execution_from_list.id, execution_by_id.id)
        self.assertEqual(execution_from_list.workflow_id,
                         execution_by_id.workflow_id)
        self.assertEqual(execution_from_list['blueprint_id'],
                         execution_by_id['blueprint_id'])

        self.assertEqual(len(delta['deployment_nodes']), 1,
                         'deployment_nodes: {0}'.format(delta))

        self.assertEqual(len(delta['node_state']), 1,
                         'node_state: {0}'.format(delta))

        self.assertEqual(len(delta['nodes']), self.expected_nodes_count,
                         'nodes: {0}'.format(delta))

        nodes_state = delta['node_state'].values()[0]
        self.assertEqual(len(nodes_state), self.expected_nodes_count,
                         'nodes_state: {0}'.format(nodes_state))
        events, total_events = self.client.events.get(execution_by_id.id)

        self.assertGreater(len(events), 0,
                           'Expected at least 1 event for execution id: {0}'
                           .format(execution_by_id.id))

        hosts = self._get_hosts(self.host_pool_service_deployment_id)
        for host in hosts:
            if UBUNTU_HOST in host.get('name'):
                self._assert_host_state(host, True)
            else:
                self._assert_host_state(host)

    def post_uninstall_assertions(self, client=None):
        client = client or self.client

        nodes_instances = client.node_instances.list(self.deployment_id)
        self.assertFalse(any(node_ins for node_ins in nodes_instances if
                             node_ins.state != 'deleted'))

    def _install_service_with_seed_vms(self):

        blueprint_path = resources.get_resource(
            'openstack-test/service-blueprint.yaml')

        self.blueprint_yaml = blueprint_path

        blueprint_id = '{0}-hps-blueprint'.format(self.test_id)
        deployment_id = '{0}-hps-deployment'.format(self.test_id)

        self.upload_deploy_and_execute_install(
            blueprint_id=blueprint_id,
            deployment_id=deployment_id,
            inputs={
                'centos_image_id': self.env.centos_7_image_id,
                'windows_image_id': self.env.windows_image_id,
                'ubuntu_image_id': self.env.ubuntu_trusty_image_id,
                'flavor_id': self.env.medium_flavor_id,
                'key_path': '/tmp/{0}.pem'.format(str(uuid.uuid4()))
            },
            execute_timeout=EXTENDED_TIMEOUT
        )

        self.host_pool_service_deployment_id = deployment_id

    def _get_hosts(self, deployment_id):
        outputs = self.get_outputs(self.host_pool_service_deployment_id)
        endpoint_url = self.get_endpoint_url(outputs)
        response = requests.get('{0}/hosts'.format(endpoint_url))
        self.logger.info('Current hosts: {0}'.format(response.json()))
        return response.json()

    def _assert_host_state(self, host, state=False):
        self.assertEquals(host.get('allocated'), state)

    def _scale(self, node_id, delta=+1):
        self.cfy.execute_workflow('scale', self.host_pool_service_deployment_id,
                                  parameters=dict(scalable_entity_name=node_id,
                                                  delta=delta))

    def _uninstall_host_pool_service(self):
        self.execute_uninstall(self.host_pool_service_deployment_id)

    @property
    def expected_nodes_count(self):
        return 5

    def get_inputs(self):

        # the host pool endpoint can be retrieved by getting the deployment
        # outputs of the host-pool-service deployment

        outputs = self.get_outputs(self.host_pool_service_deployment_id)
        endpoint_url = self.get_endpoint_url(outputs)
        inputs = {
            'host_pool_service_endpoint': endpoint_url
        }
        return inputs

    def get_outputs(self, deployment_id):
        return self.client.deployments.outputs.get(
            deployment_id=deployment_id).outputs

    def get_endpoint_ip(self, outputs):
        return outputs['endpoint']['ip_address']

    def get_endpoint_url(self, outputs):
        endpoint_url = 'http://{0}:{1}'.format(self.get_endpoint_ip(outputs),
                                               outputs['endpoint']['port'])
        return endpoint_url
