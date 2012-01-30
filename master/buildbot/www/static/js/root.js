bb.pages.root = function(next, route_matches) {
    var div = $('<div>');
    div.append('<h1>Hello</h1>');
    var ul = $('<ul>');
    div.append(ul);
    var li = $('<li>');
    ul.append(li);
    li.append(bb.link("builders", 'builders'));

    bb.display_page_content(next, div);
    return true;
}
