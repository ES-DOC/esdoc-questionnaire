/* functions specific to the editor & viewer */

var PREVIOUSLY_SELECTED_TAB = 0;

$.ui.dynatree.nodedatadefaults["icon"] = false; // Turn off icons by default

function panes(parent) {
    // hide panes by default
    // only show them as the corresponding tree node is selected
    $(parent).find(".pane").each(function() {
        $(this).hide();
    });
}

function autocompletes(parent) {
    $(".autocomplete").each(function(){
        var suggestions = $(this).attr("suggestions").split("|");
        $(this).autocomplete({
            source : suggestions
        });
    });
}

function dynamic_accordions(parent) {
   /* have to do this in two steps b/c the accordion JQuery method cannot handle any content inbetween accordion panes */
   /* but I need a container for dynamic formsets to be bound to */
   /* so _after_ multiopenaccordion() is called, I stick a div into each pane and bind the formset() method to that div */
    $(parent).find(".accordion .accordion_header").each(function() {
        var prefix = $(this).closest(".accordion").attr("name");
        var accordion_wrapper = "<div class='accordion_unit' name='" + prefix + "'></div>";
        $(this).next().andSelf().wrapAll(accordion_wrapper);
    });

    $(parent).find(".accordion_unit").each(function() {
        var prefix = $(this).closest(".accordion").attr("name");

        $(this).formset({
           prefix : prefix,
           formCssClass : "dynamic_accordion_" + prefix,
           added : function(row) {
               added_subformset_form(row);
           },
           removed : function(row) {
               removed_subformset_form(row);
           }
       });
    });
}

/*
function nullables(parent) {
    $(parent).find(".multiselect.nullable").each(function() {
        $(this).change(function() {
            console.log("getting change fn from nullable")

            var values = $(this).find("option:selected").map(function() {
                return $(this).val();
            }).get();

            if (values.indexOf("_NONE") != -1) {
                console.log("it has none as an option")
                $(this).find("option:selected").each(function() {
                    if ($(this).val()!="_NONE") {
                        console.log('found option other than none')
                        I AM HERE THIS DOESNT WORK
                        $(this).click();
                    }
                });
            }
        });
    });
}
*/

function enumerations(parent) {
    // this is a single fn for _both_ open & nullable enumerations
    $(parent).find(".multiselect.open,.multiselect.nullable").each(function() {

        // whenever this widget changes,
        // 1) check if NONE is selected
        // and if so, de-select everything else (and hide the other widget)
        // 2) check if OTHER is selected
        // and if so, show the "other" widget

        $(this).change(function() {
            other = $(this).siblings("input.other:first");
            widget = $(this).siblings(".ui-multiselect:first").find(".multiselect_content");

            var values = $(this).find("option:selected").map(function() {
                return $(this).val();
            }).get();

            if (values.indexOf("_NONE") != -1) {
               console.log("TODO: HANDLE .nullable ENUMERATIONS")
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
        $(this).trigger("change");
    });
}

function treeviews(parent) {

    $(parent).find(".treeview").each(function() {
        treeview = $(this); // to use later on...
        $(this).dynatree({
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
                selected_nodes = $(treeview).dynatree("getSelectedNodes");
                $(treeview).find(".dynatree-partsel:not(.dynatree-selected)").each(function() {
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
        root = $(this).dynatree("getRoot");
        root.visit(function(node) {
            // TODO: DON'T SELECT EVERYTHING BY DEFAULT
            node.select(true);
            node.expand(true);
        });
        // root is actually a built-in parent of the tree
        // and not the first item in my list
        // hence this fn calll
        var first_child = root.getChildren()[0];
        first_child.activate(true);

    });
    
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
            if ($(item).attr("multiple")) {
                alert("inherit multiple select")
            }
            else {
                alert("inherit single select");
            }
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

    var customizer_id = $(row).closest(".field").find("input[name='customizer_id']").val();
    var prefix        = $(row).closest(".field").find("input[name='prefix']").val()
    var n_forms       = parseInt($(row).closest(".accordion").children(".accordion_unit").length)
    var property_id   = $(row).closest(".field").find("input[name='property_id']").val()

    url = window.document.location.protocol + "//" + window.document.location.host + "/ajax/select_realization/";
    url += "?c=" + customizer_id + "&p=" + prefix + "&n=" + n_forms;
    if (property_id != "") {
        url += "&s=" + property_id;
    }

    /* TODO: DOUBLE-CHECK THAT THIS WILL WORK W/ LESS THAN 2 FORMS */
    var old_prefix = $(row).closest(".accordion").attr("name");
    old_prefix += "-" + (n_forms - 2);

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
                    init_widget(buttons,parent,true);
                    init_widget(fieldsets,parent,true);
                    init_widget(selects,parent,true);
                    init_widget(helps,parent,true);
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

                                        /* TODO: CHECK DATATYPE OF DATA? */
                                        var parsed_data = $.parseJSON(data);

                                        var new_prefix = parsed_data.prefix

                                        console.log(old_prefix);
                                        console.log(new_prefix);
                                        console.log(parsed_data);

                                        // rename ids and names
                                        update_field_names(row,old_prefix,new_prefix);
                                        populate_form(row,parsed_data);

                                        $(add_subform_dialog).dialog("close");
                                    }
                                    else {

                                        /*
                                         note - do not use a status code of 400 for form valiation errors
                                         that will be routed to the "error" event below
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
