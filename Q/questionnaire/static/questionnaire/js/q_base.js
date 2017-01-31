/* q_base.js */

/* the Q mostly uses Angular for the client */
/* preferably angular-ui-bootstrap */
/* sometimes it uses Bootstrap directly for look-and-feel stuff */
/* but sometimes, when all else fails, it uses pure JQuery or JavaScript */
/* that code is defined here */

/**************************************/
/* begin jquery widget initialization */
/**************************************/

/* b/c the Q is so dynamic, new JQuery widgets may need to be initialized at run-time */
/* these fns takes care of that */

function init_widgets(init_fn, elements, force_init) {
    force_init = typeof force_init !== 'undefined' ? force_init : false;
    var initialized_widget_class_name = "initialized_" + init_fn.name;
    $(elements).each(function() {
        if (! $(this).hasClass(initialized_widget_class_name) || (force_init)) {
            init_fn(this);
            $(this).addClass(initialized_widget_class_name)
        }
    });
}

function helps(element) {
    var help_type = $(element).attr("data-toggle").toLowerCase();
    if ( help_type == "tooltip") {
        $(element).tooltip({
            'placement': 'auto',
            'html': true
        })
    }
    else if ( help_type == "popover") {
        $(element).popover({
            'placement': 'auto',
            'html': true,
            'trigger': 'manual'
        }).click(function(e) {
            $(this).popover('toggle');
            e.preventDefault();
            e.stopPropagation();
        });
    }
    else {
        console.log("error: unknown help type: " + help_type)
    }
}

function selects(element) {
    /* this is NOT for dealing w/ enumeration fields */
    /* it is just for making standard selects a bit prettier */
    var multiple = $(element).hasClass("multiple");
    var single = $(element).hasClass("single");
    $(element).selectpicker({
        'dropupAuto': false,
        'selectedTextFormat': "count>3",
        'size': 10,
        'title': "Select Options"
    }).selectpicker('render');
}

function splitters(element) {
console.log("setup splitter")
$(element).split({orientation: "vertical"});
//    var container = $(element).closest("div.panel");
//    $(element).height(
//        $(container).height()
//    ).split({
//        orientation: "vertical",
//        limit: $(container).width() * 0.10,
//        position: "20%"
//    });
//    /* TODO: BIND THIS TO SOME REALISTIC EVENT THAT WILL BE CALLED BY THE Q */
//    $(container).resize(function() {
//        $(element).height(
//            $(this).height()
//        );
//    });
}

/**************************************/
/* end jquery widget initialization */
/**************************************/

/**************************/
/* begin message handling */
/**************************/

function show_lil_msg(content) {
    var lil_msg = $("div#lil_msg");
    $(lil_msg).html(content);
    var ms_to_show = 2600;
    $(lil_msg)
        .fadeIn()
        .delay(ms_to_show)
        .fadeOut();
};

function show_msg(text, status) {
    status = typeof status !== 'undefined' ? status : "default";
    var box = bootbox.alert(text);
    box.find(".modal-content").addClass(status);
}

function check_msg() {
    /* gets all pending Django messages */

    var messages_url = "/services/messages/";

    $.ajax({
        url: messages_url,
        type: "GET",
        cache: false,
        success: function (data) {
            $.each(data, function (i, message) {
                show_msg(message.text, message.status);
            });
        },
        error: function (xhr, status, error) {
            console.log(xhr.responseText + status + error)
        }
    });
};

/************************/
/* end message handling */
/************************/


/*********************/
/* begin utility fns */
/********************/

function sort_objects_by_attr(objs, attr) {
    sorted_objs = objs.sort(function(a, b) {
        if (a[attr] == b[attr]) { return 0; }
        if (a[attr] > b[attr]) { return 1; }
        else { return -1; }
    });
    return sorted_objs;
}

/*******************/
/* end utility fns */
/*******************/