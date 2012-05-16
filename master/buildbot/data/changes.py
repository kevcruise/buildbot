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

from twisted.internet import defer
from twisted.python import log
from buildbot.data import base, exceptions
from buildbot.process import metrics, users
from buildbot.util import datetime2epoch

def _fixChange(change):
    # TODO: make these mods in the DB API
    if change:
        change = change.copy()
        del change['is_dir']
        change['when_timestamp'] = datetime2epoch(change['when_timestamp'])
        change['link'] = base.Link(('change', str(change['changeid'])))
    return change


class Change(base.Endpoint):

    pathPattern = ( 'change', 'i:changeid' )

    def get(self, options, kwargs):
        d = self.master.db.changes.getChange(kwargs['changeid'])
        d.addCallback(_fixChange)
        return d


class Changes(base.Endpoint):

    pathPattern = ( 'change', )
    pathTopicTemplate = 'change.#' # TODO: test

    def get(self, options, kwargs):
        try:
            count = min(int(options.get('count', '50')), 50)
        except:
            return defer.fail(
                    exceptions.InvalidOptionException('invalid count option'))
        d = self.master.db.changes.getRecentChanges(count)
        @d.addCallback
        def sort(changes):
            changes.sort(key=lambda chdict : chdict['changeid'])
            return map(_fixChange, changes)
        return d

class UpdateChanges(base.UpdateMethods):

    @defer.inlineCallbacks
    def addChange(self, files=None, comments=None, author=None, revision=None,
            when_timestamp=None, branch=None, category=None, revlink='',
            properties={}, repository='', codebase=None, project='', src=None):
        metrics.MetricCountEvent.log("added_changes", 1)

        # add a source to each property
        for n in properties:
            properties[n] = (properties[n], 'Change')

        if src:
            # create user object, returning a corresponding uid
            uid = yield users.createUserObject(self, author, src)
        else:
            uid = None

        change = {
            'changeid': None, # not known yet
            'author': unicode(author),
            'files': map(unicode, files),
            'comments': unicode(comments),
            'revision': unicode(revision) if revision is not None else None,
            'when_timestamp': datetime2epoch(when_timestamp),
            'branch': unicode(branch) if branch is not None else None,
            'category': unicode(category) if category is not None else None,
            'revlink': unicode(revlink) if revlink is not None else None,
            'properties': properties,
            'repository': unicode(repository),
            'project': unicode(project),
            'codebase': '', # not known yet
            # TODO: uid
        }

        if codebase is None:
            if self.master.config.codebaseGenerator is not None:
                change['codebase'] = self.config.codebaseGenerator(change)
            else:
                change['codebase'] = ''

        # add the Change to the database
        changeid = yield self.db.changes.addChange(uid=uid, **change)

        # log, being careful to handle funny characters
        msg = u"added change with revision %s to database" % (revision,)
        log.msg(msg.encode('utf-8', 'replace'))

        # new-style notification
        self.mq.produce("change.%d.new" % changeid, change)

        defer.returnValue(changeid)
