bb.pages.notfound = function(next, route_matches) {
    var div = $('<div>');
    div.append('<h1>Not Found!</h1>');
    div.append('Sorry, the page you requested was not found');

    bb.display_page_content(next, div);
    return true;
}
