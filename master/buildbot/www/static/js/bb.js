/*  This file is part of Buildbot.  Buildbot is free software: you can
 * redistribute it and/or modify it under the terms of the GNU General Public
 * License as published by the Free Software Foundation, version 2.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc., 51
 * Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 *
 * Copyright Buildbot Team Members */

/* this file is returned in the initial page request, and is responsible for
 * loading Buildbot's requirements on demand. */

bb = {};

//
// Resource loaders
//

bb.load = {
    resources: [],
};

bb.load._get_resource = function(type, name) {
    // see if it's already loaded, and if so, return immediately
    var nresources = bb.load.resources.length;
    for (var i = 0; i < nresources; i++) {
        var r = bb.load.resources[i];
        if (r.type === 'js' && r.name === name) {
            return r;
        }
    }
};

bb.load.js = function(next, filename) {
    var r = bb.load._get_resource('js', filename);
    if (r) {
        return true; // already loaded
    }

    // otherwise, add it to the resource list
    bb.load.resources.push({
        type: 'js',
        name: filename,
        permanent: true, // js resources can't be unloaded
    });

    // and try to load it
    load(bb.baseurl + "static/js/" + filename)
        .thenRun(next);
    // TODO: error handling
};

bb.load.api = function(next, path) {
    var r = bb.load._get_resource('js', path);
    if (r) {
        return next(r.value);
    }

    var url = bb.baseurl + "api/latest/" + path;
    console.log(url);
    return next(['xxx', 'yyy']);
};

//
// Page display
//

bb.routes = [
    [ new RegExp("^/?$"), 'root.js', 'root' ],
    [ new RegExp("^/builders/?$"), 'builders.js', 'builders' ],

    // must be the last item in the list
    [ new RegExp(".*"), 'notfound.js', 'notfound' ],
];

// each page defines a function in this namespace, after it is loaded
bb.pages = {};

bb.open_current_page = function(next) {
    var url = History.getState().url;
    var path = url.replace(new RegExp('^' + bb.baseurl + 'ui'), '');

    console.log("show page " + path);

    // search for a matching URI
    var nroutes = bb.routes.length,
        route,
        matches;
    for (var i = 0; i < nroutes; i++) {
        route = bb.routes[i];
        matches = route[0].exec(path);
        if (matches) {
            break;
        }
    }

    console.log(" loading: js resource " + route[1] + ", bb.pages." + route[2]);

    run(function(next) { bb.load.js(next, route[1]); })
        .thenRun(function(next) { return bb.pages[route[2]](next, matches); })
        .thenRun(next);
    // TODO: error handling
};

bb.display_page_content = function(next, new_content) {
    $('#content').replaceWith(new_content);
    new_content.attr('id', 'content');
    return true;
}

bb.link = function(path, content) {
    var a = $('<a>')
    a.attr('href', "javascript:bb.goto_page(\'" + path + "\')"); // XXX quoting!
    a.append(content);
    return a;
}

bb.goto_page = function(path) {
    History.pushState(null, null, bb.baseurl + 'ui/' + path);
}

bb.display_header = function(next) {
    var hdr = $('<div>');
    hdr.attr('class', 'header');
    hdr.attr('id', 'header');
    hdr.append(bb.link('', 'Home'))
    hdr.append(' - ');
    hdr.append(bb.link('builders', 'Builders'))
    $('div#header').replaceWith(hdr);

    return true;
}

//
// Startup
//

$(function() {
    // register for onstatechange
    History.Adapter.bind(window,'statechange', function() {
        run(bb.open_current_page);
    });

    // and open the current page and the header
    run(bb.open_current_page,
        bb.display_header);
});
