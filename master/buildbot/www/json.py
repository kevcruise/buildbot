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

import datetime
import re
from twisted.internet import defer
from twisted.web import server
from buildbot.www import resource
from buildbot.util import json

class JsonRootResource(resource.Resource):
    version_classes = {}

    @classmethod
    def api_version(cls, version):
        def wrap_class(klass):
            cls.version_classes[version] = klass
            return klass
        return wrap_class

    def __init__(self, master):
        resource.Resource.__init__(self, master)

        min_vers = master.config.www.get('json_minimum_version', 0)
        for version, klass in self.version_classes.iteritems():
            if version >= min_vers:
                self.putChild('v%d' % version, klass(master))

        latest = max(self.version_classes.iterkeys())
        self.putChild('latest', self.version_classes[latest](master))

    def render(self, request):
        request.setHeader("content-type", 'application/json')
        return json.dumps(dict(api_versions=self.version_classes.keys()))


class JsonBaseResource(resource.Resource):
    # base class for all Json APIs

    # rather than construct the entire possible hierarchy of Json resources,
    # this is marked as a leaf node, and any remaining path items are parsed
    # during rendering
    isLeaf = True

    # a decorator to tie methods in subclasses to the paths they implement
    @staticmethod
    def path(*path_components):
        def wrap(fn):
            fn.path_components = path_components
            return fn
        return wrap

    def __init__(self, master):
        resource.Resource.__init__(self, master)

        # Set up paths for this instance. Since there is a single instance for
        # each API version, there' no reason to try to do this at the class
        # (rather than instance) level.
        self.paths = []
        for attr in dir(self):
            v = getattr(self, attr)
            if hasattr(v, 'path_components'):
                self.paths.append((v.path_components, v))

    def render(self, request):
        req_path = request.postpath
        req_path_len = len(req_path)
        for meth_path, meth in self.paths:
            if len(meth_path) != req_path_len:
                continue
            for rc, mc in zip(req_path, meth_path):
                if rc != mc and mc[0] != '$':
                    break
            else:
                break
        else:
            request.setResponseCode(404)
            request.setHeader('content-type', 'text/plain')
            return 'API resource not found'

        # got a match -- now calculate any parameters
        parameters = {}
        for rc, mc in zip(req_path, meth_path):
            if mc[0] == '$':
                parameters[mc[1:]] = rc

        self.call_method(meth, request, parameters)
        return server.NOT_DONE_YET

    def call_method(self, meth, request, parameters):
        d = defer.maybeDeferred(meth, request, **parameters)

        # format the output
        as_text = self._boolean_arg(request, 'as_text', False)
        filter = self._boolean_arg(request, 'filter', as_text)
        compact = self._boolean_arg(request, 'compact', not as_text)
        callback = request.args.get('callback', [None])[0]

        @d.addCallback
        def render_json(data):
            # set up the content type
            if as_text:
                request.setHeader("content-type", 'text/plain')
            else:
                request.setHeader("content-type", 'application/json')
                request.setHeader("content-disposition",
                            "attachment; filename=\"%s.json\"" % request.path)

            # set up caching
            cache_seconds = self.master.config.www.get('json_cache_seconds', 0)
            if cache_seconds:
                now = datetime.datetime.utcnow()
                expires = now + datetime.timedelta(seconds=cache_seconds)
                request.setHeader("Expires",
                                expires.strftime("%a, %d %b %Y %H:%M:%S GMT"))
                request.setHeader("Pragma", "no-cache")

            # filter and render the data
            if filter:
                data = self._filter_empty(data)

            if compact:
                data = json.dumps(data, sort_keys=True, separators=(',',':'))
            else:
                data = json.dumps(data, sort_keys=True, indent=2)

            if isinstance(data, unicode):
                data = data.encode("utf-8")

            if callback:
                # Only accept things that look like identifiers for now
                if re.match(r'^[a-zA-Z$][a-zA-Z$0-9.]*$', callback):
                    data = '%s(%s);' % (callback, data)
                request.setHeader("Access-Control-Allow-Origin", "*")

            request.write(data)
            request.finish()

        @d.addErrback
        def eb(f):
            request.processingFailed(f)
            return None

    def _boolean_arg(self, request, arg, default):
        value = request.args.get(arg, [default])[0]
        if value in (False, True):
            return value
        value = value.lower()
        if value in ('1', 'true'):
            return True
        if value in ('0', 'false'):
            return False
        # Ignore value.
        return default

    def _filter_empty(self, data):
        empty = ('', False, None, [], {}, ())
        if isinstance(data, (list, tuple)):
            filtered = (self._filter_empty(x) for x in data)
            return [ x for x in filtered if x not in empty ]
        elif isinstance(data, dict):
            filtered = ((k, self._filter_empty(v))
                        for (k, v) in data.iteritems())
            return dict(x for x in filtered if x[1] not in empty)
        else:
            return data


@JsonRootResource.api_version(1)
class JsonV1Resource(JsonBaseResource):

    @JsonBaseResource.path('builders')
    def json_builders(self, request):
        return ['abc', 'def']

    @JsonBaseResource.path('builders', '$builderid')
    def json_builder(self, request, builderid):
        return []
