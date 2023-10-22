# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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
'''Cloudify Host-Pool plugin package config'''


import os
import re
import pathlib

from setuptools import setup


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir, 'cloudify_hostpool_plugin/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()

setup(
    name='cloudify-host-pool-plugin',
    version=get_version(),
    license='LICENSE',
    packages=['cloudify_hostpool_plugin'],
    description='A Cloudify plugin enabling hosts acquisition '
                'via cloudify-host-pool-service',
    install_requires=[
        'cloudify-common>=4.4,<7.0.0',
        'requests>=2.25.0'
    ]
)
