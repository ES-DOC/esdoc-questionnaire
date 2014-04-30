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
                var child_item = $(child_pane).find("tr.field[name='"+item_name+"']").find("input");
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
                var child_item = $(child_pane).find("tr.field[name='"+item_name+"']").find("input,textarea");
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
