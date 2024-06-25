# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Util tests"""

from collections import namedtuple
from unittest.mock import patch
from common import util

Snicaddr = namedtuple('snicaddr',
                      ['family', 'address'])

mock_addrs = {
    'eth0': [Snicaddr(17, '00:1A:2B:3C:4D:5E')],
    'wlan0': [Snicaddr(17, '66:77:88:99:AA:BB')],
    'enp0s3': [Snicaddr(17, '11:22:33:44:55:66')]
}

@patch('psutil.net_if_addrs')
def test_get_sys_interfaces(mock_net_if_addrs):
  mock_net_if_addrs.return_value = mock_addrs
  # Expected result
  expected = {
      'eth0': '00:1A:2B:3C:4D:5E',
      'enp0s3': '11:22:33:44:55:66'
  }

  result = util.get_sys_interfaces()
  # Assert the result
  assert result == expected
