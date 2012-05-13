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

import inspect
from twisted.python import reflect
from twisted.application import service
from buildbot.util import pathmatch
from buildbot.data import exceptions, base

class DataConnector(service.Service):

    submodules = [
        'buildbot.data.changes',
    ]

    def __init__(self, master):
        self.setName('data')
        self.master = master
        self.matcher = pathmatch.Matcher()

        self._setup()

    def _setup(self):
        # gather base classes and make a new class to put at self.update
        bases = []
        for moduleName in self.submodules:
            module = reflect.namedModule(moduleName)
            for sym in dir(module):
                obj = getattr(module, sym)
                if not inspect.isclass(obj):
                    continue
                if issubclass(obj, base.UpdateMethods):
                    bases.append(obj)
                if issubclass(obj, base.Endpoint):
                    self.matcher[obj.pathPattern] = obj(self.master)

        # build an Update class and instantiate it
        Update = type('Update', tuple(bases), dict(__slots__=['master']))
        self.update = Update()
        self.update.master = self.master

    def _lookup(self, path):
        try:
            return self.matcher[path]
        except KeyError:
            raise exceptions.InvalidPathError

    def get(self, options, path):
        endpoint, kwargs = self._lookup(path)
        return endpoint.get(options, kwargs)

    def startConsuming(self, callback, options, path):
        endpoint, kwargs = self._lookup(path)
        topic = endpoint.getSubscriptionTopic(options, kwargs)
        if not topic:
            raise exceptions.InvalidPathError
        # TODO: aggregate consumers of the same topics
        # TODO: double this up with get() somehow
        return self.master.mq.startConsuming(callback, topic)

    def control(self, action, args, path):
        endpoint, kwargs = self._lookup(path)
        return endpoint.control(action, args, kwargs)
