# #######
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

'''
    tests.tasks
    ~~~~~~~~~~~
    Tests host allocation and deallocation
'''

import os
import unittest
import httplib
import requests_mock

from collections import namedtuple
from urlparse import urlparse

from cloudify.mocks import MockCloudifyContext
from cloudify_hostpool_plugin import tasks
from cloudify.exceptions import NonRecoverableError
from cloudify.state import current_ctx

HOST_ID = 12345
SERVICE_URL = 'hostpool-svc.mock.com'
SERVICE_PORT = 8080
SERVICE_ENDPOINT = 'mock://{0}:{1}'.format(SERVICE_URL, SERVICE_PORT)

MockOptions = namedtuple('MockOptions', [
    'host', 'port', 'protocol', 'host_id',
    'keyfile', 'keyfile_content',
    'username', 'password',
    'error', 'error_code', 'reason'
])


class AcquireHostTestCase(unittest.TestCase):
    '''Tests host acquire functionality'''
    def setUp(self):
        self.ctx = MockCloudifyContext(node_id='test_acquire_host',
                                       node_name='AcquireHostTestCase',
                                       runtime_properties={},
                                       properties={})
        current_ctx.set(self.ctx)
        self.service_url = SERVICE_URL
        self.service_port = SERVICE_PORT
        self.endpoint = SERVICE_ENDPOINT
        svc_urlparse = urlparse(self.endpoint)
        self.opts = MockOptions(
            host_id=HOST_ID,
            host='172.16.99.123',
            port=22,
            protocol='ssh',
            username='my-username',
            password='my-p@ssw0rd',
            keyfile=os.path.expanduser('~/.ssh/key_{0}_{1}_{2}'.format(
                svc_urlparse.hostname,
                svc_urlparse.port,
                HOST_ID)),
            keyfile_content='=====BEGIN=====SOME$TEST@DATA=====END=====',
            error='Something went wrong!',
            error_code=httplib.INTERNAL_SERVER_ERROR,
            reason='A very detailed error reason'
        )

        self.error_response = {'error': self.opts.error,
                               'code': self.opts.error_code}

    def tearDown(self):
        current_ctx.clear()
        if os.path.exists(self.opts.keyfile):
            os.unlink(self.opts.keyfile)

    @requests_mock.Mocker()
    def test_with_password_success(self, mock):
        '''POST /host/allocate with success response (using password auth)'''
        mock.register_uri(
            'POST',
            '{0}/host/allocate'.format(self.endpoint),
            json={
                'id': self.opts.host_id,
                'os': 'linux',
                'endpoint': {
                    'ip': self.opts.host,
                    'port': self.opts.port,
                    'protocol': self.opts.protocol
                },
                'credentials': {
                    'username': self.opts.username,
                    'password': self.opts.password
                }
            },
            status_code=httplib.OK
        )
        self.ctx.node.properties['os'] = 'linux'
        tasks.acquire(self.endpoint, ctx=self.ctx)
        self.assertEqual(self.ctx.instance.runtime_properties['host_id'],
                         self.opts.host_id)
        self.assertEqual(self.ctx.instance.runtime_properties['user'],
                         self.opts.username)
        self.assertEqual(self.ctx.instance.runtime_properties['password'],
                         self.opts.password)
        self.assertEqual(self.ctx.instance.runtime_properties['ip'],
                         self.opts.host)

    @requests_mock.Mocker()
    def test_with_keyfile_success(self, mock):
        '''POST /host/allocate with success response (using key auth)'''
        mock.register_uri(
            'POST',
            '{0}/host/allocate'.format(self.endpoint),
            json={
                'id': self.opts.host_id,
                'os': 'linux',
                'endpoint': {
                    'ip': self.opts.host,
                    'port': self.opts.port,
                    'protocol': self.opts.protocol
                },
                'credentials': {
                    'username': self.opts.username,
                    'key': self.opts.keyfile_content
                }
            },
            status_code=httplib.OK
        )
        self.ctx.node.properties['os'] = 'linux'
        tasks.acquire(self.endpoint, ctx=self.ctx)
        self.assertEqual(self.ctx.instance.runtime_properties['host_id'],
                         self.opts.host_id)
        self.assertEqual(self.ctx.instance.runtime_properties['user'],
                         self.opts.username)
        self.assertEqual(self.ctx.instance.runtime_properties['key'],
                         self.opts.keyfile)
        self.assertEqual(self.ctx.instance.runtime_properties['ip'],
                         self.opts.host)
        self.assertTrue(os.path.exists(self.opts.keyfile))

    @requests_mock.Mocker()
    def test_bad_os_type(self, mock):
        '''POST /host/allocate with a non-string OS type'''
        mock.register_uri(
            'POST',
            '{0}/host/allocate'.format(self.endpoint),
            status_code=httplib.BAD_REQUEST
        )
        self.ctx.node.properties['os'] = 12345
        self.assertRaisesRegexp(
            NonRecoverableError,
            'Requested OS must be a string',
            tasks.acquire,
            self.endpoint,
            ctx=self.ctx)

    @requests_mock.Mocker()
    def test_failure(self, mock):
        '''POST /hosts with failure response'''
        mock.register_uri(
            'POST',
            '{0}/host/allocate'.format(self.endpoint),
            json=self.error_response,
            status_code=self.opts.error_code
        )
        self.ctx.node.properties['os'] = 'linux'
        self.assertRaisesRegexp(
            NonRecoverableError,
            'Error: {0}, Reason: {1}'.format(
                self.opts.error_code,
                self.error_response['error']),
            tasks.acquire,
            self.endpoint,
            ctx=self.ctx)


class ReleaseHostTestCase(unittest.TestCase):
    '''Tests host release functionality'''
    def setUp(self):
        self.ctx = MockCloudifyContext(node_id='test_acquire_host',
                                       node_name='AcquireHostTestCase',
                                       runtime_properties={})
        current_ctx.set(self.ctx)
        self.service_url = SERVICE_URL
        self.service_port = SERVICE_PORT
        self.endpoint = SERVICE_ENDPOINT
        self.opts = MockOptions(
            host_id=HOST_ID,
            host='172.16.99.123',
            port=22,
            protocol='ssh',
            username='my-username',
            password='my-p@ssw0rd',
            keyfile=os.path.expanduser('~/.ssh/key_{0}'.format(HOST_ID)),
            keyfile_content='=====BEGIN=====SOME$TEST@DATA=====END=====',
            error='Something went wrong!',
            error_code=httplib.INTERNAL_SERVER_ERROR,
            reason='A very detailed error reason'
        )

        self.error_response = {'error': self.opts.error,
                               'code': self.opts.error_code}

    def tearDown(self):
        current_ctx.clear()
        if os.path.exists(self.opts.keyfile):
            os.unlink(self.opts.keyfile)

    @requests_mock.Mocker()
    def test_success(self, mock):
        '''DELETE /host/<host_id>/deallocate with success response'''
        with open(self.opts.keyfile, 'w') as f_key:
            f_key.write(self.opts.keyfile_content)
        self.ctx.instance.runtime_properties['host_id'] = self.opts.host_id
        self.ctx.instance.runtime_properties['key'] = self.opts.keyfile

        mock.register_uri(
            'DELETE',
            '{0}/host/{1}/deallocate'.format(
                self.endpoint, self.opts.host_id),
            json={},
            status_code=httplib.NO_CONTENT
        )

        tasks.release(self.endpoint, ctx=self.ctx)
        self.assertFalse(os.path.exists(self.opts.keyfile))

    @requests_mock.Mocker()
    def test_failure(self, mock):
        '''DELETE /host/<host_id>/deallocate with failure response'''
        self.ctx.instance.runtime_properties['host_id'] = self.opts.host_id
        mock.register_uri(
            'DELETE',
            '{0}/host/{1}/deallocate'.format(
                self.endpoint, self.opts.host_id),
            json=self.error_response,
            status_code=self.opts.error_code
        )
        self.assertRaisesRegexp(
            NonRecoverableError,
            'Error: {0}, Reason: {1}'.format(
                self.opts.error_code,
                self.error_response['error']),
            tasks.release,
            self.endpoint,
            ctx=self.ctx)
