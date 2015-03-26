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
import unittest

import json
import requests
import requests_mock

from cloudify.mocks import MockCloudifyContext
from cloudify_hostpool_plugin import tasks
from cloudify.exceptions import NonRecoverableError


class TestTasks(unittest.TestCase):
    """ Host Pool plugin tasks unit test. Mocks all http requests."""

    def setUp(self):
        self.ctx = MockCloudifyContext(node_id='test_id',
                                       node_name='test_name',
                                       runtime_properties={})
        self.service_url = 'http://test_url'
        self.error = 'Something went wrong'
        self.error_code = requests.codes.INTERNAL_SERVER_ERROR
        self.reason = 'reason'
        self.username = 'username'
        self.password = 'password'
        self.host = 'ip'
        self.host_id = 'host_id'
        self.port = 'port'
        self.keyfile = os.path.expanduser(
            '~/.ssh/key_{0}'.format(self.host_id))
        self.key_content = 'secure key'
        self.good_response_acquire_password = {'host': self.host,
                                               'port': self.port,
                                               'host_id': self.host_id,
                                               'auth': {
                                                   'username': self.username,
                                                   'password': self.password
                                               }}
        self.good_response_acquire_key = {'host': self.host,
                                          'port': self.port,
                                          'host_id': self.host_id,
                                          'auth': {
                                              'username': self.username,
                                              'keyfile': self.keyfile
                                          }}
        self.error_response = {'error': self.error,
                               'code': self.error_code}

    def tearDown(self):
        if os.path.exists(self.keyfile):
            os.unlink(self.keyfile)

    def test_acquire_good_response(self):
        with requests_mock.mock() as m:
            m.post('{0}/hosts'.format(self.service_url),
                   content=json.dumps(self.good_response_acquire_password),
                   status_code=requests.codes.CREATED)
            tasks.acquire(self.service_url, ctx=self.ctx)
        self.assertEqual(self.ctx.instance.runtime_properties['user'],
                         self.username)
        self.assertEqual(self.ctx.instance.runtime_properties['password'],
                         self.password)
        self.assertEqual(self.ctx.instance.runtime_properties['ip'], self.host)

    def test_acquire_good_response_key(self):
        with requests_mock.mock() as m:
            m.post('{0}/hosts'.format(self.service_url),
                   content=json.dumps(self.good_response_acquire_key),
                   status_code=requests.codes.CREATED)
            tasks.acquire(self.service_url, ctx=self.ctx)
        self.assertEqual(self.ctx.instance.runtime_properties['user'],
                         self.username)
        self.assertEqual(self.ctx.instance.runtime_properties['key'],
                         self.keyfile)
        self.assertEqual(self.ctx.instance.runtime_properties['ip'], self.host)
        self.assertTrue(os.path.exists(self.keyfile))

    def test_acquire_error_response(self):
        with requests_mock.mock() as m:
            m.post('{0}/hosts'.format(self.service_url),
                   content=json.dumps(self.error_response),
                   status_code=self.error_code)
            self.assertRaisesRegexp(
                NonRecoverableError,
                'Error: {0} Reason: {1}'.format(
                    self.error_code,
                    self.error_response['error']),
                tasks.acquire,
                self.service_url,
                ctx=self.ctx)

    def test_acquire_bad_response(self):
        with requests_mock.mock() as m:
            m.post('{0}/hosts'.format(self.service_url),
                   content="",
                   status_code=self.error_code,
                   reason=self.reason)
            self.assertRaisesRegexp(
                NonRecoverableError,
                'Error: {0} Reason: {1}'.format(
                    self.error_code,
                    self.reason),
                tasks.acquire,
                self.service_url,
                ctx=self.ctx)

    def test_release_good_response(self):
        with open(self.keyfile, 'w') as f:
            f.write(self.key_content)
        service_url = 'http://test_url'
        self.ctx.instance.runtime_properties['host'] = \
            self.good_response_acquire_key
        self.ctx.instance.runtime_properties['key'] = self.keyfile
        with requests_mock.mock() as m:
            m.delete('{0}/hosts/{1}'.format(service_url, self.host_id),
                     content=json.dumps(self.good_response_acquire_key),
                     status_code=requests.codes.OK)
            tasks.release(service_url, ctx=self.ctx)
        self.assertFalse(os.path.exists(self.keyfile))

    def test_release_bad_response(self):
        self.ctx.instance.runtime_properties['host'] = \
            self.good_response_acquire_key
        with requests_mock.mock() as m:
            m.delete('{0}/hosts/{1}'.format(self.service_url, self.host_id),
                     content="",
                     status_code=self.error_code,
                     reason=self.reason)
            self.assertRaisesRegexp(
                NonRecoverableError,
                'Error: {0} Reason: {1}'.format(
                    self.error_code,
                    self.reason),
                tasks.release,
                self.service_url,
                ctx=self.ctx)
