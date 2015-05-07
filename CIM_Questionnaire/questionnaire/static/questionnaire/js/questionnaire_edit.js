/* functions specific to the editor & viewer */

var PREVIOUSLY_SELECTED_TAB = 0;

$.ui.dynatree.nodedatadefaults["icon"] = false; // Turn off icons by default


function panes(element) {
    // hide panes by default
    // only show them as the corresponding tree node is selected
    $(element).hide();
}


function autocompletes(element) {
    /* an autocomplete field stores the options as an attribute */
    /* parse those options and pass them to JQuery */
    var suggestions = $(element).attr("suggestions").split("|");
    $(element).autocomplete({
        source : suggestions
    });
    /* then add a visual indication that the field supports autocompletion */
    /* I use a standard JQuery icon, but move it down and left so that it resides w/in the field */
    $(element).after(
        "<span class='ui-icon ui-icon-carat-1-s' style='display: inline-block; margin-left: -16px; margin-bottom: -8px;' title='this field supports autocompletion'></span>"
    );
}


function dynamic_accordion_buttons(element) {

    if ( $(element).hasClass("add")) {
        $(element).button({
            icons: { primary : "ui-icon-circle-plus" },
            text: true
        }).click(function(event) {
            var max = $(event.target).prevAll("input[name='max']").val();
            var accordion = $(event.target).closest("div.add").prev(".accordion");
            var n_accordion_panes = $(accordion).find(".accordion_unit").length;
            if (n_accordion_panes == max) { // don't need to explicitly check where max="*" b/c this comparison will still be untrue

                $("#confirm_dialog").html("Unable to add; this would create more than the maxium number of instances.");
                $("#confirm_dialog").dialog("option", {
                    title: "add",
                    dialogClass: "no_close",
                    height: 200,
                    width: 400,
                    buttons: {
                        ok: function () {
                            $(this).dialog("close");
                        }
                    }
                }).dialog("open");

            }
            else {

                var dynamic_formset_add_button = $(event.target).closest("div.add").prev(".accordion").find(".add-row:last");
                $(dynamic_formset_add_button).click();
                // there is function bound to the dynamic-formset add event that will fire after that button is pressed
                // (I don't have to explicitly call add_subform)

            }

        });
    }

    if ( $(element).hasClass("remove")) {
        $(element).button({
            icons: { primary: "ui-icon-circle-minus" },
            text: true
        });
        /* the click event had to move to its own fn ("remove_subform" defined in questionnaire_edit.js) */
    }

    if ( $(element).hasClass("replace")) {
        $(element).button({
            icons: { primary : "ui-icon-refresh" },
            text: true
        }).click(function(event) {

            var accordion = $(event.target).closest(".form").find(".accordion:first");

            $("#confirm_dialog").html("This will remove the current instance and replace it with either an existing or new instance.  You will be unable to undo this operation.  Are you sure you want to continue?");
            $("#confirm_dialog").dialog("option", {
                title: "replace",
                dialogClass: "no_close",
                height: 200,
                width: 400,
                buttons: {
                    yes : function () {

                        var dynamic_formset_remove_button = $(accordion).find(".delete-row:last");
                        $(dynamic_formset_remove_button).click();
                        var dynamic_formset_add_button = $(accordion).find(".add-row:last");
                        $(dynamic_formset_add_button).click();

                        $(this).dialog("close")

                    },
                    no : function() {

                        $(this).dialog("close");

                    }
                }
            }).dialog("open");

        });

    }
}


function dynamic_accordions(element) {
    /* element = $(parent).find(".accordion .accordion_header") */
    /* have to do this in two steps b/c the accordion JQuery method cannot handle any content inbetween accordion panes */
    /* but I need a container for dynamic formsets to be bound to */
    /* so _after_ multiopenaccordion() is called, I stick a div into each pane and bind the formset() method to that div */
    var prefix = $(element).closest(".accordion").attr("name");

    $(element).next().andSelf().wrapAll("<div class='accordion_unit' name='" + prefix + "'></div>");

    var accordion_unit = $(element).closest(".accordion_unit");

    $(accordion_unit).formset({
       prefix : prefix,
       formCssClass : "dynamic_accordion_" + prefix,  /* note that formCssClass is _required_ in this situation */
       added : function(row) {
           added_subformset_form(row);
       },
       removed : function(row) {
           removed_subformset_form(row);
       }
   });

}


function accordion_headers(element) {

    /* updates the accordion headers based on the current value of a scientific property */

    $(element).find(".atomic_value").each(function () {
        $(this).trigger("change");
    });
    $(element).find(".ui-multiselect").each(function () {
        console.log("found it");
        var source_name = $(this).prev(".multiselect").attr("name");
        var target_name = source_name.replace("-enumeration_value", "-scientific_property_value");
        $(this).find(".multiselect_header").change(function (event) {
            var source_value = $(this).button("option", "label");
            var target = $("*[name='" + target_name + "']");
            $(target).val(source_value);
        })
    });
}


var enumeration_null_value = "_NONE";
var enumeration_other_value = "_OTHER";

function enumerations(element) {

    var header = $(element).find(".multiselect_header");
    var content = $(element).find(".multiselect_content");

    var other = $(element).siblings("input.other:first");

    $(other).focus(function() {
        /* make enumeration_other selectable by clicking */
        /* _but_ break out of it if you do other things w/ the mouse */
        $(this).one("mouseup", function() {
            $(this).select();
            return false;
        }).select();
    });

    $(element).on("multiselect_change", function(e) {

        /* whenever this element changes, */
        /* check if NONE is selected and if so, de-select everything else (and hide the other widget) */
        /* check if OTHER is selected and if so, show the "other" widget */

        var selected_items = $(content).find("li input:checked");
        var selected_items_values = $(selected_items).map(function () {
            return $(this).val();
        }).get();

        if (selected_items_values.indexOf(enumeration_null_value) != -1) {

            $(selected_items).each(function() {
                if ($(this).val() != enumeration_null_value) {
                    $(this).prop("checked", false);
                    $(this).parents("li:first").removeClass("selected");
                    /* I'll wind up w/ circular events if I simulate clicking */
                    /* $(this).click(); */
                }
            });
            $(other).hide();
            multiselect_set_label(element, header, content);
        }

        else if (selected_items_values.indexOf(enumeration_other_value) != -1) {
            $(other).show();
        }
        else {
            $(other).hide();
        }

    });

    /* force enumeration code to run on initialization */
    $(element).trigger("multiselect_change");
}


function treeviews(element) {

    $(element).dynatree({
        debugLevel      : 0,
        checkbox        : true,
        selectMode      : 3,
        minExpandLevel  : 1,
        activeVisible   : true,
        onActivate      : function(node) {
            show_pane(node.data.key);
        },
        onDeactivate    : function(node) {
            var inactive_pane_id = node.data.key + "_pane";
            var inactive_pane = $("#"+inactive_pane_id);
            $(inactive_pane).hide();
            PREVIOUSLY_SELECTED_TAB = $(inactive_pane).find(".tabs:first").tabs("option","active");
        }
        ,
        onSelect        : function(flag,node) {
            selected_nodes = $(element).dynatree("getSelectedNodes");
            $(element).find(".dynatree-partsel:not(.dynatree-selected)").each(function () {
                var node = $.ui.dynatree.getNode(this);
                selected_nodes.push(node);
            })

            node.tree.visit(function (node) {
                var pane_id = node.data.key + "_pane";
                var pane = $("#" + pane_id);
                if ($.inArray(node, selected_nodes) > -1) {
                    $(pane).removeClass("ui-state-disabled");
                    $(pane).find("input[name$='-active']").prop("checked", true)
                }
                else {
                    $(pane).addClass("ui-state-disabled");
                    $(pane).find("input[name$='-active']").prop("checked", false)
                }
            });
        }
    });

    var root = $(element).dynatree("getRoot");

    root.visit(function(node) {
        var pane_id = node.data.key + "_pane";
        var pane = $("#"+pane_id);

        var active_checkbox = $(pane).find("input[name$='-active']");

//        if ($(active_checkbox).is(":checked")) {
//            console.log(pane_id + " is selected");
//            node.select(true);
//        }
//        else {
//            console.log(pane_id + " is NOT selected");
//        }
//        else {
//            node.select(false);
//        }
//        alert(pane_id + ": " + $(active_checkbox).is(":checked"));
//        node.select($(active_checkbox).is(":checked"));
        node.select(true);
//        node.select(false)
//        node.activate($(active_checkbox).is(":checked"))
        node.expand(true);
    });
    // root is actually a built-in parent of the tree, and not the first item in my list
    // hence this fn call
    var first_child = root.getChildren()[0];
    first_child.activate(true);
}


function show_pane(pane_key) {
    var pane = $("#" + pane_key + "_pane");

    if (!$(pane).hasClass("loaded")) {

        toastr.info("loading...");

        var project_name = $("#_project_name").val();
        var instance_key = $("#_instance_key").val();
        var section_key = $(pane).attr("data-section-key");

        /* get_form_section_view is the name of the AJAX view to return the particular type of form (new vs existing, edit vs customize) */
        /* for this template; it is set in the template header */
        var url = window.document.location.protocol + "//" + window.document.location.host + "/api/" + project_name + "/" + get_form_section_view+ "/" + section_key;
        url += "?instance_key=" + instance_key;

        $.ajax({
            url: url,
            type: "GET",
            success: function (data) {

                $(pane).html(data);
                $(pane).ready(function () {

                    var parent = $(pane);
                    init_widgets(tabs, $(parent).find(".tabs"));
                    init_widgets(helps, $(parent).find(".help_button"));
                    init_widgets(dates, $(parent).find(".datetime, .date"));
                    init_widgets(expanders, $(parent).find(".default, .character"));
                    init_widgets(autocompletes, $(parent).find(".autocomplete"));
                    init_widgets(multiselects, $(parent).find(".multiselect"));
                    init_widgets(buttons, $(parent).find("input.button"));
                    init_widgets(enumerations, $(parent).find(".enumeration"));
                    init_widgets(accordions, $(parent).find(".accordion").not(".fake"));
                    init_widgets(dynamic_accordions, $(parent).find(".accordion .accordion_header"));
                    init_widgets(accordion_buttons, $(parent).find(".subform_toolbar button"));
                    init_widgets(dynamic_accordion_buttons, $(parent).find("button.add, button.remove, button.replace"));
                    init_widgets(fieldsets, $(parent).find(".collapsible_fieldset"));
                    init_widgets(inherits, $(parent).find(".inherited"));
                    init_widgets(changers, $(parent).find(".changer"));  /* force the change event on scientific properties, which copies the property value to the accordion header */

                    // identify the section as loaded for js...
                    $(pane).addClass("loaded");
                    // and for the django view...
                    $(pane).find("input#id_"+pane_key+"-loaded").prop('checked', true);
                    /* TODO: SINCE I'M LOADING AN ENTIRE PANE, JUST SET ALL LOADED FLAGS TO TRUE */
                    /* TODO: IN THE LONGTERM, THOUGH, I OUGHT TO BE MORE PRECISE HERE */
                    $(pane).find("input[name$='-loaded']").prop("checked", true);

                });
            toastr.clear();
            }
        });

    }
    $(pane).show();
    /* make sure that whichever sub-tab had been selected gets activated once this pane is displayed */
    $(pane).find(".tabs:first").tabs({ "active" : PREVIOUSLY_SELECTED_TAB });
}


function inherits(element) {
    var tree_widget = $("#component_tree").find(".treeview");
    if (!tree_widget.length) {
        /* there is no point of inheriting anything in the absence of a component tree */
        return true
    }
    var tree = $(tree_widget).dynatree("getTree");
    var inheritance_options = $(element).closest(".field").find("div.inheritance_options:first");

    var current_pane = $(element).closest(".pane");
    var current_component_key = $(current_pane).attr("id").replace(/_pane$/, "")
    var current_component_node = tree.getNodeByKey(current_component_key);
    var child_component_keys = [];
    current_component_node.visit(function (node) {
        child_component_keys.push(node.data.key)
    });

    if ($(element).hasClass("multiselect")) {
        $(element).on("multiselect_change", function() {
            if ($(inheritance_options).find(".enable_inheritance").is(":checked")) {

                var source_element_id = $(element).find("div.multiselect_content ul:first").attr("id");
                var target_element_ids_to_inherit_later = new Array();

                $(child_component_keys).each(function () {
                    var child_pane = $(".pane[id='" + this + "_pane']");
                    var target_element_id = source_element_id.replace(current_component_key, this);
                    if ($(child_pane).hasClass("loaded")) {
                        var target_element = $(child_pane).find("#"+target_element_id).closest("div.multiselect");
                        inherit_now(element, target_element);
                    }
                    else {
                        /* the pane has not yet been loaded, so inherit it later */
                        target_element_ids_to_inherit_later.push(target_element_id);
                    }
                });

                if (target_element_ids_to_inherit_later.length) {
                    inherit_later(element, target_element_ids_to_inherit_later);
                }
            }
        });

    }
    else {
        $(element).change(function () {

            if ($(inheritance_options).find(".enable_inheritance").is(":checked")) {

                var source_element_id = $(element).attr("id");
                var target_element_ids_to_inherit_later = new Array();

                $(child_component_keys).each(function () {
                    var child_pane = $(".pane[id='" + this + "_pane']");
                    var target_element_id = source_element_id.replace(current_component_key, this);
                    if ($(child_pane).hasClass("loaded")) {
                        /* the inherited field will exist in the pane, so inherit it now */
                        var target_element = $(child_pane).find("#"+target_element_id);
                        inherit_now(element, target_element);
                    }
                    else {
                        /* the pane has not yet been loaded, so inherit it later */
                        target_element_ids_to_inherit_later.push(target_element_id);
                    }
                });

                if (target_element_ids_to_inherit_later.length) {
                    inherit_later(element, target_element_ids_to_inherit_later)
                }
            }
        });
    }
}


function inherit_now(source_element, target_element) {
    var target_inheritance_options = $(target_element).closest(".field").find("div.inheritance_options:first");
    if ($(target_inheritance_options).find(".enable_inheritance").is(":checked")) {

        /* element_type can be a...
         checkbox input,
         a normal input (including ".other"),
         a select,
         a textarea,
         a single multiselect,
         or a multiple multiselect,
        */

        var element_type = $(source_element).prop("tagName").toLowerCase();

        if (element_type == "input") {
            if ($(source_element).attr("type") == "checkbox") {
                $(target_element).prop("checked", $(source_element).is(":checked"));
            }
            else {
                $(target_element).val($(source_element).val());
                if ($(source_element).hasClass("other")) {
                    $(target_element).show();
                }
            }
        }

        else if (element_type == "select") {
            $(target_element).val($(source_element).val());
        }

        else if (element_type == "textarea") {
            $(target_element).val($(source_element).val())
        }

        else if ($(source_element).hasClass("multiselect")) {
            /* TODO: THIS WILL NOT WORK W/ SORTABLE MULTISELECTS */
            /* TODO: BUT I DON'T THINK THAT FEATURE IS EVER USED */
            /* TODO: SO JUST GET RID OF THAT FEATURE */
            var source_inputs = $(source_element).find("div.multiselect_content li input");
            var target_inputs = $(target_element).find("div.multiselect_content li input");
            $(source_inputs).each(function(input_index, source_input) {
                var target_input = $(target_inputs).eq(input_index);
                $(target_input).prop("checked", $(source_input).prop("checked"))
                $(target_input).trigger("change")
            });
            /* .other is handled above by <input>*/
            /* var other_source_input = $(source_element).siblings("input.other:first") */
            /* var other_target_input = $(target_element).siblings("input.other:first") */
            /* $(other_target_input).val($(other_source_input).val()); */
        }

        else {
            console.log("ERROR: unhandled element type (" + element_type + ") for inheritance.");
        }
    }
}


function inherit_later(source_element, target_element_ids) {
    /* note that target_element_ids is an array; */
    /* I am doing this all-at-once, instead of one-at-a-time */
    /* (as w/ inherit_now), to avoid multiple AJAX calls */

    var inheritance_data = {
        "instance_key": $("input#_instance_key").val()
    };

    var element_type = $(source_element).prop("tagName").toLowerCase();

    if (element_type == "input") {
        if ($(source_element).attr("type") == "checkbox") {
            $(target_element_ids).each(function() {
                inheritance_data[this] = $(source_element).is(":checked");
            });
        }
        else {
            $(target_element_ids).each(function() {
                inheritance_data[this] = $(source_element).val();
            });
        }
    }

    else if (element_type == "select") {
        $(target_element_ids).each(function() {
            inheritance_data[this] = $(source_element).val();
        });
    }

    else if (element_type == "textarea") {
        $(target_element_ids).each(function() {
            inheritance_data[this] = $(source_element).val();
        });
    }

    else if ($(source_element).hasClass("multiselect")) {
        var source_component_key = $(source_element).closest("div.pane").attr("id").replace(/_pane$/, "");
        var component_key_regex = /^id_(.*?)_standard_properties/;
        

        var source_content = $(source_element).find("div.multiselect_content");
        $(source_content).find("li input").each(function() {
            var source_input = this;
            $(target_element_ids).each(function() {
                var target_component_key = component_key_regex.exec(this)[1];
                var target_key = $(source_input).attr("id").replace(source_component_key, target_component_key)
                inheritance_data[target_key] = $(source_input).is(":checked");
            });
        });
    }

    var url = window.document.location.protocol + "//" + window.document.location.host + "/api/add_inheritance_data/";

    $.ajax({
        url: url,
        type: "POST",
        data: inheritance_data,
        cache: false,
        error: function(xhr, status, error) {
            console.log(xhr.responseText + status + error)
        }
    });
}


function add_subform(row) {

    /* this takes place AFTER the form is added */

    var field                   = $(row).closest(".field");
    var accordion               = $(row).closest(".accordion");
    var is_one_to_one           = $(accordion).hasClass("fake");
    var is_one_to_many          = !(is_one_to_one);
    var pane                    = $(row).closest(".pane");
    var accordion_units         = $(accordion).children(".accordion_unit");
    var customizer_id           = $(field).find("input[name='customizer_id']").val();
    var property_id             = $(field).find("input[name='property_id']").val();
    var prefix                  = $(field).find("input[name='prefix']").val();
    var parent_vocabulary_key   = $(pane).find("input[name$='-vocabulary_key']:first").val();
    var parent_component_key    = $(pane).find("input[name$='-component_key']:first").val();
    var n_forms                 = parseInt(accordion_units.length);
    var existing_subforms       = $(accordion_units).find("input[name$='-id']:first").map(function() {
        var removed = $(this).closest(".accordion_content").find(".remove:first input[name$='-DELETE']").val();
        if (!removed) {
            var subform_id = $(this).val();
            if (subform_id != "") {
                return parseInt(subform_id)
            }
        }
    }).get();

    var url = window.document.location.protocol + "//" + window.document.location.host + "/ajax/select_realization/";
    url += "?c=" + customizer_id + "&p=" + prefix + "&n=" + n_forms + "&e=" + existing_subforms + "&p_v_k=" + parent_vocabulary_key + "&p_c_k=" + parent_component_key;
    if (property_id != "") {
        url += "&s=" + property_id;
    }

    var old_prefix = $(accordion).attr("name");
    /* TODO: DOUBLE-CHECK THAT THIS IS ALWAYS CREATING A NEWFORM W/ ID=0 */
    /*old_prefix += "-" + (n_forms - 2);*/
    old_prefix += "-" + "0";

    var add_subform_dialog = $("#add_dialog");

    $.ajax({
        url     : url,
        type    : "GET",
        cache   : false,
        success : function(data) {
            $(add_subform_dialog).html(data);
            $(add_subform_dialog).dialog("option",{
                height      : 300,
                width       : 600,
                dialogClass : "no_close",
                title       : "Select an instance to add",
                open : function() {
                    // apply all of the JQuery code to _this_ dialog
                    var parent = $(add_subform_dialog);
                    // the addition of the 'true' attribute forces initialization,
                    // even if this dialog is opened multiple times
                    init_widgets(buttons, $(parent).find("input.button"), true);
                    init_widgets(fieldsets, $(parent).find(".collapsible_fieldset"), true);
                    init_widgets(helps, $(parent).find(".help_button"), true);
                    init_widgets(multiselects, $(parent).find(".multiselect"), true);
                },

                buttons : [
                    {
                        text : "ok",
                        click : function() {

                            var add_subform_data = $(this).find("#select_realization_form").serialize();
                            $.ajax({
                                url     : url,
                                type    : "POST",  // (POST mimics submit)
                                data    : add_subform_data,
                                cache   : false,
                                error   : function(xhr,status,error) {
                                    console.log(xhr.responseText + status + error);
                                },
                                success : function(data,status,xhr) {

                                    var status_code = xhr.status;

                                    if (status_code == 200 ) {

                                        var parsed_data = $.parseJSON(data);
                                        var new_prefix = parsed_data.prefix;
                                        var new_label = parsed_data.label;

                                        /* rename ids and names */
                                        update_field_names(row,old_prefix,new_prefix);
                                        /* insert data */
                                        populate_form(row,parsed_data);
                                        /* make sure that all 'loaded' fields are set to true */
                                        $(row).find("input[name$='-loaded']").prop("checked", true);
                                        /* update label */
                                        $(row).find(".accordion_header:first .label").html(new_label);

                                        /* initialize JQuery widgets */
                                        $(row).ready(function() {

                                            if (is_one_to_many) {
                                                init_widgets_on_show(fieldsets, $(row).find(".collapsible_fieldset"))
                                                init_widgets_on_show(helps, $(row).find(".help_button"));
                                                init_widgets_on_show(readonlies, $(row).find(".readonly"));
                                                init_widgets_on_show(dates, $(row).find(".datetime,.date"));
                                                init_widgets_on_show(accordions, $(row).find(".accordion").not(".fake"));
                                                init_widgets_on_show(dynamic_accordions, $(row).find(".accordion .accordion_header"));
                                                init_widgets_on_show(accordion_buttons, $(row).find(".subform_toolbar button"));
                                                init_widgets_on_show(dynamic_accordion_buttons, $(row).find("button.add,button.remove,button.replace"));
                                                init_widgets_on_show(multiselects, $(row).find(".multiselect"));
                                                init_widgets_on_show(enumerations, $(row).find(".enumeration"));
                                                init_widgets_on_show(autocompletes, $(row).find(".autocomplete"));
                                                init_widgets_on_show(enablers, $(row).find(".enabler"));
                                            }

                                            else if (is_one_to_one) {
                                                init_widgets(fieldsets, $(row).find(".collapsible_fieldset"))
                                                init_widgets(helps, $(row).find(".help_button"));
                                                init_widgets(readonlies, $(row).find(".readonly"));
                                                init_widgets(dates, $(row).find(".datetime,.date"));
                                                init_widgets(accordions, $(row).find(".accordion").not(".fake"));
                                                init_widgets(dynamic_accordions, $(row).find(".accordion .accordion_header"));
                                                init_widgets(accordion_buttons, $(row).find(".subform_toolbar button"));
                                                init_widgets(dynamic_accordion_buttons, $(row).find("button.add,button.remove,button.replace"));
                                                init_widgets(multiselects, $(row).find(".multiselect"));
                                                init_widgets(enumerations, $(row).find(".enumeration"));
                                                init_widgets(autocompletes, $(row).find(".autocomplete"));
                                                init_widgets(enablers, $(row).find(".enabler"));
                                            }

                                            else {
                                                console.log("unable to determine if this is a one-to-one or a one-to-many subform; cannot initialize jquery widgets");
                                            }



                                        });

                                        $(add_subform_dialog).dialog("close");

                                    }
                                    else {

                                        /*
                                         note - do not use a status code of 400 for form valiation errors
                                         that will be routed to the "error" event above
                                         instead use some valid success code other than 200 (202, for example)
                                        */

                                        var msg = xhr.getResponseHeader("msg");
                                        var msg_dialog = $(document.createElement("div"));
                                        msg_dialog.html(msg);
                                        msg_dialog.dialog({
                                            modal: true,
                                            title : "error",
                                            hide: "explode",
                                            height: 200,
                                            width: 400,
                                            // I'm only ever showing a dialog box if there was an error in the POST
                                            // TODO: ENSURE THE ERROR CLASS PROPAGATES TO ALL CHILD NODES?
                                            dialogClass: "no_close ui-state-error",
                                            buttons: {
                                                OK: function () {
                                                    $(this).dialog("close");
                                                }
                                            }
                                        });

                                        $(add_subform_dialog).html(data);
                                        // re-apply all of the JQuery code to _this_ dialog
                                        var parent = $(add_subform_dialog);
                                        // the addition of the 'true' attribute forces initialization,
                                        // even if this dialog is opened multiple times
                                        init_widgets(buttons, $(parent).find("input.button"), true);
                                        init_widgets(fieldsets, $(parent).find(".collapsible_fieldset"), true);
                                        init_widgets(multiselects, $(parent).find(".multiselect"), true);
                                        init_widgets(helps, $(parent).find(".help_button"), true);
                                    }
                                }
                            })
                        }
                    },
                    {
                        text : "cancel",
                        click : function() {

                            var dynamic_formset_remove_button = $(row).find(".delete-row:first");
                            $(dynamic_formset_remove_button).click();

                            $(add_subform_dialog).dialog("close");
                        }
                    }
                ],
                close   : function() {
                    $(this).dialog("close");
                }
            }).dialog("open");
        }
    });
}


function remove_subform(remove_button) {

    /* this takes place BEFORE the form is removed */

    var min = $(remove_button).prevAll("input[name='min']").val();
    var accordion = $(remove_button).closest(".accordion");
    var n_accordion_panes = $(accordion).find(".accordion_unit").length;
    if (n_accordion_panes == min) {

        $("#confirm_dialog").html("Unable to remove; this would result in less than the minumum number of instances.");
        $("#confirm_dialog").dialog("option", {
            title: "remove",
            dialogClass: "no_close",
            height: 200,
            width: 400,
            buttons: {
                ok: function () {
                    $(this).dialog("close");
                }
            }
        }).dialog("open");

    }
    else {

        $("#confirm_dialog").html("Removing this will delete the relationship but not the underlying instance.  Do you wish to continue?.");
        $("#confirm_dialog").dialog("option", {
            title: "remove",
            dialogClass: "no_close",
            height: 200,
            width: 400,
            buttons: {
                yes: function () {
                    var dynamic_formset_remove_button = $(remove_button).closest(".accordion_content").next(".delete-row:first");
                    $(dynamic_formset_remove_button).click();
                    // there is function bound to the dynamic-formset remove event that will fire after that button is pressed
                    // (I don't have to explicitly call anything)
                    $(this).dialog("close")
                },
                no: function () {
                    $(this).dialog("close")
                }
            }
        }).dialog("open");
    }
}


function added_subformset_form(row) {
    add_subform(row);
}


function removed_subformset_form(row) {
    // don't have to do anything else
}
