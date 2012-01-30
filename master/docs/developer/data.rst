Data API
========

The data layer combines access to stored state and messages, ensuring consistency between them, and exposing a well-defined API that can be used both internally and externally.
Using caching and the clock information provided by the db and mq layers, this layer ensures that its callers can easily receive a dump of current state plus changes to that state, without missing or duplicating messages.

Sections
--------

The data api is divided into four sections:

 * getters - fetching data from the db API, and
 * subscriptions - subscribing to messages from the mq layer;
 * control -  allows state to be changed in specific ways by sending appropriate messages (e.g., stopping a build); and
 * update - direct updates to state appropriate messages.

The getters and subscriptions are exposed everywhere.
Access to the control section should be authenticated at higher levels, as the data layer does no authentication.
The updates section is for use only by the process layer.

The interfaces for all sections but the update sections are intended to be language-agnostic.  That is, they should be callable from JavaScript via HTTP, or via some other interface added to Buildbot after the fact.

Getter
++++++

The getter section can get either a single resource, or a list of resources.
Getting a single resource requires a resource identifier (a tuple of strings) and a set of options to support automatic expansion of links to other resources (thus saving round-trips).
Lists are requested with a partial resource identifier (a tuple of strings) and an optional set of filter options.
In some cases, certain filters are implicit in the path, e.g., the list of buildsteps for a particular build.

Subscriptions
+++++++++++++

Message subscriptions can be made to anything that can be listed or gotten from the getter sections, using the same resource identifiers.
Options and explicit filters are not supported - a message contains only the most basic information about a resource, and a list subscription results in a message for every new resource of the desired type.
Implicit filters are supported.

Control
+++++++

The control sections defines a set of actions that cause Buildbot to behave in a certain way, e.g., rebuilding a build or shutting down a slave.
Actions correspond to a particular resource, although sometimes that resource is the root resource (an empty tuple).

Update
++++++

The update sections defines a free-form set of methods that Buildbot's process implementation calls to update data.
Most update methods both modify state via the db API and send a message via the mq API.
Some are simple wrappers for these APIs, while others contain more complex logic, e.g., building a source stamp set for a collection of changes.
This section is the proper place to put common functionality, e.g., rebuilding builds or assembling buildsets.

Concrete Interfaces
-------------------

Python Interface
++++++++++++++++

.. py:module:: buildbot.data.connector

Within the buildmaster process, the root of the data API is available at `self.master.data`, which is a :py:class:`DataConnector` instance.

.. py:class:: DataConnector

    The first three sections are implemented with the :py:meth:`get`, :py:meth:`startConsuming`, and :py:meth:`control` methods, while the update section is implemented using the :py:attr:`update` attribute.
    The ``path`` arguments to these methods should always be tuples.
    Integer arguments can be presented as either integers or strings that can be parsed by ``int``; all other arguments must be strings.

    .. py:method:: get(options, path)

        :param options: dictionary containing model-specific options
        :param path: a tuple describing the resource to get
        :raises: :py:exc:~buildbot.data.exceptions.InvalidPathError
        :returns: a resource or list via Deferred, or None

        This method implements the getter section.
        Depending on the path, it will return a single resource or a list of resources.
        If a single resource is not specified, it returns ``None``.

        The options argument can be used to filter lists of resources, or to affect the amount of associated data returned with a single resource.

        The return value is composed of simple Python objects - lists, dicts, strings, numbers, and None, along with :py:class:`~buildbot.data.base.Link` instances giving paths to other resources.

    .. py:method:: startConsuming(callback, options, path)

        :param callback: a function to call for each message
        :param options: dictionary containing model-specific options
        :param path: a tuple describing the resource to subscribe to
        :raises: :py:exc:~buildbot.data.exceptions.InvalidPathError

        This method implements the subscriptions section.
        The callback interface is the same as that of :py:meth:`~buildbot.mq.connector.MQConnector.startConsuming`.
        The ``path`` argument is automatically translated into an appropriate topic.

    .. py:method:: control(action, args, path)

        :param action: a short string naming the action to perform
        :param args: dictionary containing arguments for the action
        :param path: a tuple describing the resource to act on
        :raises: :py:exc:~buildbot.data.exceptions.InvalidPathError
        :returns: a resource or list via Deferred, or None

        This method implements the getter section.
        Depending on the path, it will return a single resource or a list of resources.
        If a single resource is not specified, it returns ``None``.

Updates
.......

The update section is available at `self.master.data.update`, and contains a number of ad-hoc methods needed by the process modules.

..
    TODO: document it

Links
.....

.. py:module:: buildbot.data.base

.. py:class:: Link

    A link giving the path for this or another object.  Instances of this class
    should be serialized appropriately for the medium, e.g., URLs in an HTTP
    API.

    .. py:attribute:: path

        The path, represented as a list of path elements.


Exceptions
..........

.. py:module:: buildbot.data.exceptions

.. py:exception:: DataException

    This is a base class for all other Data API exceptions

.. py:exception:: InvalidPathError

    The path argument was invalid or unknown.

.. py:exception:: InvalidOptionError

    A value in the ``options`` argument was invalid or ill-formed.

Web Interface
+++++++++++++

The HTTP interface is implemented by the :py:mod:`buildbot.www` package, as configured by the user.
Part of that configuration is a base URL, which is considered a prefix for all paths mentioned here.

This version of the API is rooted at ``api/v2`` [#apiv1]_.
A GET operation on any path under the root gets a request.
The following query arguments are available everywhere (with the boolean arguments accepting ``0``, ``false``, ``1``, and ``true``):

 * ``as_text`` - if true, the result is returned as type text/plain, and thus easily readable in a web browser.
 * ``filter`` - if true, or if omitted and ``as_text`` is set true, empty values (empty lists and objects, false, null, and the empty string) are omitted from the result.
 * ``compact`` - if true, or if omitted and ``as_text`` is false, the returned JSON will have unnecessary whitespace stripped.
 * ``callback`` - if given, a JSONP response will be returned with this callback name.

Other query arguments are passed to the resource identified by the path, and have the meanings described in :ref:`Data Model`.

The interface is easily used with common tools like curl:

.. code-block:: none

    dustin@cerf ~ $ curl http://euclid.r.igoro.us:8010/api/v2/change/1?as_text=1
    {
      "author": "Dustin J. Mitchell <dustin@mozilla.com>",
      "branch": "master",
      "changeid": 1,
      "comments": "changed",
      "files": [
        "README.txt"
      ],
      "project": "foo",
      "repository": "/home/dustin/code/buildbot/t/testrepo/",
      "revision": "5a8a560adade3d3be6c5cb09e6e1581dd307a4bd",
      "when_timestamp": 1335680458
    }

.. _Data Model:

Data Model
----------

The data api enforces a strong and well-defined model on Buildbot's data.
This model is influenced by REST, in the sense that it defines resources, representations for resources, and identifiers for resources.
For each resource type, the API specifies

 * the attributes of the resource and their types (e.g., changes have a string specifying their project);
 * the format of links to other resources (e.g., buildsets to sourcestamp sets);
 * the events that can occur on that resource (e.g., a buildrequest can be claimed); and
 * options and filters for getting resources.

Paths are described here as separated by slashes.
The translation to tuples and other formats should be obvious.

.. toctree::
    :maxdepth: 1

    rtype-change

.. [#apiv1] The JSON API defined by ``status_json.py`` in Buildbot-0.8.x is considered version 1, although its root path was ``json``, not ``api/v1``.
