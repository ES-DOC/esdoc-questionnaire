/* functions specific to the editor & viewer */

var PREVIOUSLY_SELECTED_TAB = 0;

$.ui.dynatree.nodedatadefaults["icon"] = false; // Turn off icons by default

function panes(element) {
    // hide panes by default
    // only show them as the corresponding tree node is selected
    $(element).hide();
}

function autocompletes(parent) {
    var suggestions = $(element).attr("suggestions").split("|");
    $(elment).autocomplete({
        source : suggestions
    });
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
};

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
       formCssClass : "dynamic_accordion_" + prefix,
       added : function(row) {
           added_subformset_form(row);
       },
       removed : function(row) {
           removed_subformset_form(row);
       }
   });

}

function accordion_headers(element) {

    /* updates the accordion headers based on the current value of a scientific property
     */
    $(element).find(".atomic_value").each(function () {
        $(this).trigger("change");
    });
    $(element).find(".ui-multiselect").each(function () {
        console.log("found it");
        var source_name = $(this).prev(".multiselect").attr("name");
        var target_name = source_name.replace("-enumeration_value", "-scientific_property_value")
        $(this).find(".multiselect_header").change(function (event) {
            var source_value = $(this).button("option", "label");
            var target = $("*[name='" + target_name + "']");
            $(target).val(source_value);
        })
    });
}

/*
function nullables(element) {
    // no longer need this fn;
    // it's handled by multiselect plugin
}
*/

function enumerations(element) {
    // this is a single fn for _both_ open & nullable enumerations

    // whenever this widget changes,
    // 1) check if NONE is selected
    // and if so, de-select everything else (and hide the other widget)
    // 2) check if OTHER is selected
    // and if so, show the "other" widget

    $(element).change(function() {
        other = $(this).siblings("input.other:first");
        widget = $(this).siblings(".ui-multiselect:first").find(".multiselect_content");

        var values = $(this).find("option:selected").map(function() {
            return $(this).val();
        }).get();

        if (values.indexOf("_NONE") != -1) {
           $(widget).find("label").each(function(){
              if ($(this).hasClass("selected")) {
                  var value = $(this).find("input").val();
                  if (value != "_NONE") {
                      $(this).click()
                  }
                  $(other).hide()
              }
           });
        }

        else if (values.indexOf("_OTHER") != -1) {
            $(other).show();
        }
        else {
            $(other).hide();
        }

    });

    // and do these checks upon initialization too
    $(element).trigger("change");
}

function treeviews(element) {

    $(element).dynatree({
        debugLevel      : 0,
        checkbox        : true,
        selectMode      : 3,
        minExpandLevel  : 1,
        activeVisible   : true,
        onActivate      : function(node) {
            active_pane_id = node.data.key + "_pane";
            active_pane = $("#"+active_pane_id);
            $(active_pane).show();
            $(active_pane).find(".tabs:first").tabs({"active":PREVIOUSLY_SELECTED_TAB});
        },
        onDeactivate    : function(node) {
            inactive_pane_id = node.data.key + "_pane";
            inactive_pane = $("#"+inactive_pane_id);
            $(inactive_pane).hide();
            PREVIOUSLY_SELECTED_TAB = $(inactive_pane).find(".tabs:first").tabs("option","active");
        },
        onSelect        : function(flag,node) {
            selected_nodes = $(element).dynatree("getSelectedNodes");
            $(element).find(".dynatree-partsel:not(.dynatree-selected)").each(function() {
                var node = $.ui.dynatree.getNode(this);
                selected_nodes.push(node);
            })

            node.tree.visit(function(node) {
               pane_id = node.data.key + "_pane" ;
               pane = $("#"+pane_id);
               if ($.inArray(node,selected_nodes)>-1) {
                    $(pane).removeClass("ui-state-disabled");
                    $(pane).find("input[name$='-active']").prop("checked",true)
               }
               else {
                   $(pane).addClass("ui-state-disabled");
                   $(pane).find("input[name$='-active']").prop("checked",false)
               }
            });
        }
    });
    root = $(element).dynatree("getRoot");
    root.visit(function(node) {
        // TODO: DON'T SELECT EVERYTHING BY DEFAULT
        node.select(true);
        node.expand(true);
    });
    // root is actually a built-in parent of the tree, and not the first item in my list
    // hence this fn call
    var first_child = root.getChildren()[0];
    first_child.activate(true);

}

function inherit(item) {

    inheritance_options = $(item).nextAll(".inheritance_options:first");
    if ($(inheritance_options).find(".enable_inheritance").is(":checked")) {
        var item_name = $(item).closest("tr.field").attr("name");

        var current_pane = $(item).closest(".pane");
        var current_component_key = $(current_pane).attr("id").replace(/_pane$/,"")

        var tree = $("#component_tree").find(".treeview").dynatree("getTree");
        var current_component_node = tree.getNodeByKey(current_component_key);

        var child_pane_keys  = [];
        current_component_node.visit(function(node) {
            child_pane_keys.push(node.data.key+"_pane")
        });

        if ($(item).attr("type") == "checkbox") {
            // checkbox
            var item_value = $(item).is(":checked");
            $(child_pane_keys).each(function() {
                var child_pane = $(".pane[id='"+this+"']");
                var child_item = $(child_pane).find("tr.field[name='"+item_name+"']").find("input:first");
                if ($(child_item).next(".inheritance_options").find(".enable_inheritance").is(":checked")) {
                    $(child_item).prop("checked",item_value);
                }
            });
        }
        else if ($(item).prop("tagName").toLowerCase()=="select") {
            // TODO
            /*
            if ($(item).attr("multiple")) {
                alert("inherit multiple select")
            }
            else {
                alert("inherit single select");
            }
            */
        }
        else {
            // text input or textarea
            var item_value = $(item).val();
            $(child_pane_keys).each(function() {
                var child_pane = $(".pane[id='"+this+"']");
                var child_item = $(child_pane).find("tr.field[name='"+item_name+"']").find("input:first,textarea:first");
                if ($(child_item).next(".inheritance_options").find(".enable_inheritance").is(":checked")) {
                    $(child_item).val(item_value);
                    if ($(child_item).hasClass("enumeration_other")) {
                        $(child_item).show();
                    }
                }
            });
        }
    }

};

function add_subform(row) {

    /* this takes place AFTER the form is added */

    var field                   = $(row).closest(".field");
    var accordion               = $(row).closest(".accordion");
    var is_one_to_one           = $(accordion).hasClass("fake");
    var is_one_to_many          = !(is_one_to_one);
    var pane                    = $(row).closest(".pane");
    var accordion_units         = $(accordion).children(".accordion_unit");
    var customizer_id           = $(field).find("input[name='customizer_id']").val();
    var property_id             = $(field).find("input[name='property_id']").val()
    var prefix                  = $(field).find("input[name='prefix']").val()
    var parent_vocabulary_key   = $(pane).find("input[name$='-vocabulary_key']:first").val()
    var parent_component_key    = $(pane).find("input[name$='-component_key']:first").val()
    var n_forms                 = parseInt(accordion_units.length)
    var existing_subforms       = $(accordion_units).find("input[name$='-id']:first").map(function() {
        var removed = $(this).closest(".accordion_content").find(".remove:first input[name$='-DELETE']").val()
        if (!removed) {
            var subform_id = $(this).val();
            if (subform_id != "") {
                return parseInt(subform_id)
            }
        }
    }).get()

    url = window.document.location.protocol + "//" + window.document.location.host + "/ajax/select_realization/";
    url += "?c=" + customizer_id + "&p=" + prefix + "&n=" + n_forms + "&e=" + existing_subforms + "&p_v_k=" + parent_vocabulary_key + "&p_c_k=" + parent_component_key;
    if (property_id != "") {
        url += "&s=" + property_id;
    }

    var old_prefix = $(accordion).attr("name");
    /* TODO: DOUBLE-CHECK THAT THIS IS ALWAYS CREATING A NEWFORM W/ ID=0 */
    /*old_prefix += "-" + (n_forms - 2);*/
    old_prefix += "-" + "0"

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
                    init_widgets(buttons,$(parent).find("input.button"),true);
                    init_widgets(fieldsets,$(parent).find(".collapsible_fieldset"),true);
                    init_widgets(helps,$(parent).find(".help_button"),true);
                    init_widgets(selects,$(parent).find(".multiselect"),true);
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
                                                init_widgets_on_show(selects, $(row).find(".multiselect"));
                                                init_widgets_on_show(enumerations, $(row).find(".multiselect.open,.multiselect.nullable"));
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
                                                init_widgets(selects, $(row).find(".multiselect"));
                                                init_widgets(enumerations, $(row).find(".multiselect.open,.multiselect.nullable"));
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
                                        // TODO
                                        init_widget(buttons,parent,true);
                                        init_widget(fieldsets,parent,true);
                                        init_widget(selects,parent,true);
                                        init_widget(helps,parent,true);

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
};


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
