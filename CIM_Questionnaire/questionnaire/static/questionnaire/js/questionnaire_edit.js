/* functions specific to the editor & viewer */


$.ui.dynatree.nodedatadefaults["icon"] = false; // Turn off icons by default

function panes(parent) {
    // hide panes by default
    // only show them as the corresponding tree node is selected
    $(parent).find(".pane").each(function() {
        $(this).hide();
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
                $(active_pane).show()

            },
            onDeactivate    : function(node) {
                inactive_pane_id = node.data.key + "_pane";
                inactive_pane = $("#"+inactive_pane_id);
                $(inactive_pane).hide()
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
        var first_child = root.getChildren()[0];
        first_child.activate(true);

    });
    
}