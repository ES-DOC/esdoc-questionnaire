/* js common to entire questionnaire */
/* (no ng code here) */


/******************/
/* begin messages */
/******************/


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


/****************/
/* end messages */
/****************/


/**************************************/
/* begin jquery widget initialization */
/**************************************/


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
    var element_type = $(element).attr("data-toggle").toLowerCase();
    if ( element_type == "tooltip") {
        $(element).tooltip({
            'placement': 'auto',
            'html': true
        })
    }
    else if ( element_type == "popover") {
        $(element).popover({
            'placement': 'auto',
            'html': true,
            'trigger': 'manual'
        }).click(function(e) {
            $(this).popover('toggle');
            e.preventDefault();
        });
    }
    else {
        console.log("error: unknown help type: " + element_type)
    }
}


function selects(element) {
    var multiple = $(element).hasClass("multiple");
    /* var single = $(element).hasClass("single"); */
    $(element).selectpicker({
        'dropupAuto': false,
        'selectedTextFormat': "count>3",
        'title': "Select Options"
        /* I AM HERE */
    })
}

/************************************/
/* end jquery widget initialization */
/************************************/


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


/********************/
/* end utility fns */
/********************/