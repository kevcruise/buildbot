bb.pages.builders = function(next, route_matches) {
    var div = $('<div>');
    div.append('<h1>Builders</h1>');

    got_builders = function(next, builders) {
        //var ul = $('<ul>');
        console.log(builders);
        $.each(builders, function (i, b) {
            //var li = $('<li>');
            //div.append(b);
            //ul.append(li);
        });
        //div.append(ul);
        bb.display_page_content(next, div);
    };
    bb.load.api(got_builders, 'builders');
};


// WIP:
// * figuring out how to do async request
// * need to get rid of chain.js deps - use jquery directly instead, or something deferred-like
