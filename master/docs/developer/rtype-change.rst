Changes
=======

.. bb:rtype:: change

    :attr integer changeid: the ID of this change
    :attr string author: the author of the change
    :attr files: source-code filenames changed
    :type files: list of strings
    :attr string comments: user comments
    :attr string revision: revision for this change, or none if unknown
    :attr timestamp when_timestamp: time of the change
    :attr string branch: branch on which the change took place, or none for the "default branch", whatever that might mean
    :attr string category: user-defined category of this change, or none
    :attr string revlink: link to a web view of this change, or none
    :attr object properties: user-specified properties for this change, represented as an object mapping keys to tuple (value, source)
    :attr string repository: repository where this change occurred
    :attr string project: user-defined project to which this change corresponds
    :attr string codebase: codebase in this repository
    :attr Link link: link for this change (omitted in :bb:event:`change.$changeid.new` messages)

    TODO: uid

    A change resource represents a change to the source code monitored by Buildbot.

    .. bb:rpath:: /change

        :opt count: number of changes to return (maximum 50)

        This path lists changes, sorted by ID.
        The ``count`` option can be used to limit the number of changes.

        .. bb:event:: /change new

            :routing_key change.$changeid.new:

            TODO: this should be ```change.new`` to match the path

            A new change has been added to the cluster.

            The message contains

    .. bb:rpath:: /change/:changeid

        :pathkey integer changeid: the ID of the change
        :event new: the change has just been added

