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

class FakeUpdateComponent(object):
    pass

class FakeDataConnector(object):

    # TODO: when this is actually used, it should work as follows:
    # - use the real implementation (including endpoints) for getters
    #   and subscriptions
    # - implement fake update, control
    # - expose insertTestData

    def __init__(self, master):
        self.master = master
        self.update = FakeUpdateComponent()
        self.update.master = master

    def get(self, options, path):
        pass

    def startConsuming(self, callback, options, path):
        return self.master.mq.startConsuming('x') # ugh..

    def control(self, action, args, path):
        pass
