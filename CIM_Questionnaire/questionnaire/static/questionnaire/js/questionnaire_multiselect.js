/* custom JQuery code to support multiselects */

var multiselect_empty_multiple_text = "Select options";
var multiselect_empty_single_text = "Select option";
var multiselect_num_to_show = 2; /* number of selected entries to show in the header */

function multiselect_set_label(element, header, content) {

    var is_multiple = $(element).hasClass("multiple");

    var selected_items = $(content).find("li").has("input:checked").map(function () {
        return '"' + $(this).text().trim() + '"';
    }).get();
    var num_selected_items = selected_items.length;
    if (num_selected_items == 0) {
        var new_label = is_multiple ? multiselect_empty_multiple_text : multiselect_empty_single_text;
    }
    else if (num_selected_items <= multiselect_num_to_show) {
        var new_label = selected_items.join(", ")
    }
    else {
        var new_label = selected_items.slice(0, multiselect_num_to_show).join(", ")
                + " + " + (num_selected_items - multiselect_num_to_show) + " more";
    }

    $(header).button("option", "label", new_label);
}


function create_multiselect(element) {

    var header = $(element).find(".multiselect_header");
    var content = $(element).find(".multiselect_content");

    var start_open = $(element).hasClass("start_open");
    var is_multiple = $(element).hasClass("multiple");
    var is_sortable = $(element).hasClass("sortable");
    var is_enumeration = $(element).hasClass("enumeration");
    var is_required = $(element).hasClass("selection_required");

    /* hide the content before proceeding */
    if (! start_open) {
        $(content).hide();
    }

    /* setup the header */
    $(header).button({
        icons: {
          primary: start_open ? "ui-icon-triangle-1-e" : "ui-icon-triangle-1-s"
        },
        label: is_multiple ? multiselect_empty_multiple_text : multiselect_empty_single_text,
        text: true
    }).click(function(event) {

        var icon = $(this).find(".ui-icon:first");

        $(icon).toggleClass("ui-icon-triangle-1-s ui-icon-triangle-1-e");
        $(content).toggle();

        /* if you click outside of the mutliselect, close it */
        event.stopPropagation();
        $("html").on('click', function (event) {
            /* most of the online documentation will suggest using the "one()" JQuery function */
            /* this forces the event handler to run only once */
            /* but that will turn it off after the first click, which is not what I want to do */
            /* I want it to run last click */
            /* hence my use of "on()" above and "off()" below */
            var element_is_multiselect_option = $(event.target).closest(".multiselect_content").length;
            if (!element_is_multiselect_option) {
                $(icon).removeClass("ui-icon-triangle-1-s");
                $(icon).addClass("ui-icon-triangle-1-e");
                $(content).hide();
                $("html").off( event );
            }
        });
    });

    /* setup the content */
    $(content).find("li").each(function() {
        var content_item = this;
        var content_input = $(content_item).find("input");

        /* setup the content initially */
        if ($(content_input).prop("checked")) {
            $(content_item).addClass("selected");
        }

        /* and respond to changing content */
        $(content_input).change(function() {
            if (is_multiple) {
                $(content_item).toggleClass("selected");
            }
            else {
                /* need to do a bit more in the non-multiple section, in-case I am de-selecting */
                var input_selected = $(this).prop("checked");
                $(content).find("li").each(function () {
                    if ($(this).hasClass("selected")) {
                        $(this).removeClass("selected");
                    }
                });
                if (input_selected) {
                    $(content_item).addClass("selected");
                }
            }

            /* now that the content has changed, */
            /* set the header text and update enumeration-specific stuff */
            multiselect_set_label(element, header, content);
            if (is_enumeration) {
                $(element).trigger("multiselect_change")
            }
        });
    });

    /* make sure I can de-select non-multiple items */
    if (! is_multiple && ! is_required) {
        $(content).find("li input").deselectable();
    }

    /* some one-off code for sortable multiselects */
    if (is_sortable) {
        var sortable_icon = $("<span style='float: right;' class='ui-icon ui-icon-arrow-2-n-s' title='drag and drop to reorder'/>");
        $(content).find("label").append(sortable_icon);
        $(content).find("ul").sortable({
            axis: "y",
            placeholder: "sortable_item",
            start: function (e, ui) {
                ui.placeholder.height(ui.item.height());
                ui.placeholder.width("400");
            }
        });
    }

    /* set the header text during initialization */
    multiselect_set_label(element, header, content);
}
