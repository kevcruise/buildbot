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

import os
from twisted.python import util
from buildbot.www import resource

html = """\
<!DOCTYPE html>
<html>
    <head>
        <title></title>
        <link rel="stylesheet" type="text/css"
              href="%(baseurl)sstatic/css/default.css" />
        <script src="%(baseurl)sstatic/js/deps/load-min.js"
                type="text/javascript"></script>
        <script src="%(baseurl)sstatic/js/deps/jquery-1.4.4.min.js"
                type="text/javascript"></script>
        <script src="%(baseurl)sstatic/js/deps/jquery.history.js"
                type="text/javascript"></script>
        <script src="%(baseurl)sstatic/js/bb.js"
                type="text/javascript"></script>
        <script type="text/javascript">
            bb.baseurl = "%(baseurl)s";
        </script>
    </head>
  <body class="interface">

    <div id="header" class="header">
    </div>
    <hr />
    <div id="content" class="content">
    </div>
    </body>
</html>
"""

class UIResource(resource.Resource):
    isLeaf = True

    def __init__(self, master):
        resource.Resource.__init__(self, master)

        self.jsdir = os.path.join(util.sibpath(__file__, 'static'), 'js')

    def render(self, request):
        contents = dict(
            baseurl = self.baseurl)
        return html % contents
