/* custom JQuery code to support multiselects */

var multiselect_empty_multiple_text = "Select options";
var multiselect_empty_single_text = "Select option";
var multiselect_num_to_show = 2; /* number of selected entries to show in the header */

function get_multiselect_value(element) {
    var content = $(element).find(".multiselect_content");
    var selected_items = $(content).find("li").has("input:checked").map(function() {
        return '"' + $(this).text().trim() + '"';
    }).get();
    return selected_items;
}


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

    /* I HAVE NO IDEA WHY THIS IS MATCHING MULTIPLE HEADERS ?!? */
    /*$(header).button("option", "label", new_label);*/
    /* BUT CHANGING THE TEXT EXPLICITLY LIKE THIS WORKS */
    /* (SEE #395) */
    //$(header).find(".ui-button-text").text(new_label);
    $(element).find(".ui-button-text").each(function() {
        //console.log("before set label: " + $(element).find(".ui-button-text").text());
        $(this).text(new_label);
        //console.log("after set label: " + $(element).find(".ui-button-text").text());

    });

    /* update accordion headers for scientific_properties... */
    var is_scientific_property = $(element).closest("div.scientific_property").length;
    if (is_scientific_property) {
        var value_label = $(element).closest("div.accordion_content").prev(".accordion_header").find("input[name$='-scientific_property_value']");  /* might be more intuitive to use ".closest('div.accordion_unit')", but that may not exist depending on when the accordions are initialized via JQuery */

        if (new_label == multiselect_empty_single_text || new_label == multiselect_empty_multiple_text) {
            /* if no selection has been made, remove the label */
            $(value_label).val("");
        }
        else {
            /* if a selection has been made, update the labebl */
            $(value_label).val(new_label);
        }
    }
}


function create_multiselect(element) {

    var header = $(element).find(".multiselect_header:first");
    var content = $(element).find(".multiselect_content:first");

    var start_open = $(element).hasClass("start_open");
    var is_multiple = $(element).hasClass("multiple");
    var is_sortable = $(element).hasClass("sortable");
    var is_enumeration = $(element).hasClass("enumeration");
    var is_required = $(element).hasClass("selection_required");



    /* clear any old bindings in case this fn gets called when a new subform is added */
    /* (multiselects are weird like that) */
    $(element).unbind();
    $(header).unbind();
    $(content).unbind();

    /* hide the content before proceeding */
    if (! start_open) {
        $(content).hide();
    }
    //alert("one");
    //console.log(header);
    //console.log($(header).find("ui-button-text").text());
    /* setup the header */
    $(header).one("create_button", function() {
        //console.log("before: " + $(this).attr("class"));
        $(this).unbind();
        $(this).button({
            icons: {
                primary: start_open ? "ui-icon-triangle-1-e" : "ui-icon-triangle-1-s"
            },
            label: is_multiple ? multiselect_empty_multiple_text : multiselect_empty_single_text,
            text: true
        }).click(function(event) {

            // as per #376, do allow the content to display
            // (other code prevents readonly content from being selected)
            //if ($(element).hasClass("ui-state-disabled")) {
            //    /* don't allow changing values for readonly properties */
            //    return;
            //}

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
        //console.log("after: " + $(this).attr("class"));
    });
    $(header).trigger("create_button");
    //$(header).button({
    //    icons: {
    //      primary: start_open ? "ui-icon-triangle-1-e" : "ui-icon-triangle-1-s"
    //    },
    //    label: is_multiple ? multiselect_empty_multiple_text : multiselect_empty_single_text,
    //    text: true
    //}).click(function(event) {
    //    console.log(this)
    //
    //    // as per #376, do allow the content to display
    //    // (other code prevents readonly content from being selected)
    //    //if ($(element).hasClass("ui-state-disabled")) {
    //    //    /* don't allow changing values for readonly properties */
    //    //    return;
    //    //}
    //
    //    var icon = $(this).find(".ui-icon:first");
    //
    //    $(icon).toggleClass("ui-icon-triangle-1-s ui-icon-triangle-1-e");
    //
    //    $(content).toggle();
    //
    //    /* if you click outside of the mutliselect, close it */
    //    event.stopPropagation();
    //    $("html").on('click', function (event) {
    //        /* most of the online documentation will suggest using the "one()" JQuery function */
    //        /* this forces the event handler to run only once */
    //        /* but that will turn it off after the first click, which is not what I want to do */
    //        /* I want it to run last click */
    //        /* hence my use of "on()" above and "off()" below */
    //        var element_is_multiselect_option = $(event.target).closest(".multiselect_content").length;
    //        if (!element_is_multiselect_option) {
    //            $(icon).removeClass("ui-icon-triangle-1-s");
    //            $(icon).addClass("ui-icon-triangle-1-e");
    //            $(content).hide();
    //            $("html").off( event );
    //        }
    //    });
    //});
    //alert("two");
    /* setup the content */
    $(content).find("li").each(function() {
        var content_item = this;
        var content_input = $(content_item).find("input");

        /* THIS IS THE HACKIEST HACK IN ALL OF HACKVILLE */
        /* in theory, the value of multiselect_inputs ought to be copied over */
        /* by django-dynamic-formsets via the 'keepFieldValues' param */
        /* but that doesn't seem to be working */
        /* so I explicitly reset it here */
        /* see #395 */

        if (! $(content_input).val() ) {
            var reset_value = $.trim($(content_item).text());
            if (reset_value === "---OTHER---") {
                reset_value = "_OTHER";
            }
            else if (reset_value === "---NONE---") {
                reset_value = "_NONE";
            }
            $(content_input).val(reset_value);
        }

        $(content_input).unbind();

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
                $(element).trigger("multiselect_change");
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
