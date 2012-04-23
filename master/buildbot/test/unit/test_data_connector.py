# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

import mock
from twisted.trial import unittest
from twisted.internet import defer
from buildbot.data import connector, base
from buildbot.test.fake import fakemaster

class DataConnector(unittest.TestCase):

    def setUp(self):
        self.master = fakemaster.make_master()
        self.data = connector.DataConnector(self.master)

    def patchFooPattern(self):
        rtype = mock.create_autospec(base.Endpoint, instance=True)
        rtype.get.return_value = defer.succeed(9999)
        self.data.matcher[('foo', ':fooid', 'bar')] = rtype
        return rtype

    def test_sets_master(self):
        self.assertIdentical(self.master, self.data.master)

    def test_get(self):
        rtype = self.patchFooPattern()
        d = self.data.get({'option': '1'}, ('foo', '10', 'bar'))

        @d.addCallback
        def check(gotten):
            self.assertEqual(gotten, 9999)
            rtype.get.assert_called_once_with({'option' : '1'},
                                              {'fooid' : '10'})
        return d

    def test_startConsuming(self):
        pass # TODO

    def test_control(self):
        rtype = self.patchFooPattern()

        d = self.data.control('foo!', {'arg': 2}, ('foo', '10', 'bar'))

        @d.addCallback
        def check(gotten):
            self.assertEqual(gotten, 9999)
            rtype.control.assert_called_once_with('foo!', {'arg' : 1},
                                                        {'fooid' : '10'})
        return d
