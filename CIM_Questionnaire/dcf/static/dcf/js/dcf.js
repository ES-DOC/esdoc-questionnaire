
var PREVIOUSLY_SELECTED_TAB = 0;

var FUNCTION_QUEUE = $({});

var INITIALIZED = 0;

function enableDCF() {

    $(function() {

        /* BEGIN enable ajax access to the same domain */

        $.ajaxSetup({
            headers: { "X-CSRFToken": getCookie("csrftoken") }
        });

        /* END enable ajax access to the same domain */

        /* BEGIN enable the dialog boxes */
        

        var msg_dialog = $("#msg").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        // have to do a bit more setup of the msg dialog to customize its title
        // (see http://bugs.jqueryui.com/ticket/6016)
        msg_dialog.data( "uiDialog" )._title = function(title) {
            title.html( this.options.title );
        };
        msg_dialog.dialog('option', 'title', '<span class="ui-icon ui-icon-notice"></span>');

        $("#help-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#confirm-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#edit-dialog").dialog({
           autoOpen:false,hide:'explode',modal:true
        });
        $("#add-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#remove-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#saved-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#published-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });

        /* END enable the dialog boxes */

        /* BEGIN enable fancy buttons */

        $(".button").button();

        $("#user a").button();
        
        /* buttons for manipulating accordions */

        $(".subform-toolbar button").mouseover(function() {
            $(this).css('cursor', 'pointer');
        });
        $(".subform-toolbar button.expand" ).button({
             icons : {primary: "ui-icon-circle-triangle-s"},
             text : true
        }).click(function(event) {
            var accordion = $(event.target).closest(".subform-toolbar").nextAll(".accordion:first");
            // I have to do this manually (rather than w/ the active:all option)
            // b/c the content between accordions messes things up
            $(accordion).find(".accordion-content").show();
            $(accordion).find(".accordion-header").each(function() {
                var accordionHeaderIcon = $(this).find("span.ui-icon");
                $(accordionHeaderIcon).addClass("ui-icon-triangle-1-s");
                $(accordionHeaderIcon).removeClass("ui-icon-triangle-1-e");
            });
        });
        $(".subform-toolbar button.collapse" ).button({
            icons : {primary: "ui-icon-circle-triangle-n"},
            text: true
        }).click(function(event) {
            var accordion = $(event.target).closest(".subform-toolbar").nextAll(".accordion:first");
            // I have to do this manually (rather than w/ the active:none option)
            // b/c the content between accordions messes things up
            $(accordion).find(".accordion-content").hide();
            $(accordion).find(".accordion-header").each(function() {
                var accordionHeaderIcon = $(this).find("span.ui-icon");
                $(accordionHeaderIcon).removeClass("ui-icon-triangle-1-s");
                $(accordionHeaderIcon).addClass("ui-icon-triangle-1-e");
            });
        });

        $(".subform-toolbar button.sort").button({
            icons : { primary : "ui-icon-arrowthick-2-n-s"},
            text : true
        }).click(function(event) {
            var menu = $(this).next(".sort_by").show().position({
                my : "left top", at : "left bottom", of : this
            });
            $(document).one("click",function() {
                $(menu).hide();
            });
            return false;
        });
        $(".sort_by").each(function() {
            var sort_button = $(this).prev(".sort");
            $(this).menu().width("8em").hide();
        });
        $(".sort_by").click(function(event){
            var sort_key = $(event.target).attr("name");
            var items_to_sort = $(event.target).closest(".tab_content").find(".accordion:first");
            sort_accordions(items_to_sort,sort_key);        // call the sort fn with the specified key & target
            $(event.target).closest(".sort_by").hide();     // hide the sort_by menu
            event.preventDefault();                         // don't actually follow the menu link (one of these is bound to work)
            return false;                                   // don't actually follow the menu link (one of these is bound to work)
        });
        
        /* help-buttons (icons masquerading as buttons) */

        $(".help-button").mouseover(function() {
            $(this).css('cursor', 'pointer');
        });
        $(".help-button").hover(
            function() {
                $(this).children(".ui-icon-info").addClass('hover-help-icon');
            },
            function() {
                $(this).children(".ui-icon-info").removeClass('hover-help-icon');
            }
        );
        $(".help-button").click(function() {
           /* I escape any periods that may be in the ids (unlikely) so that JQuery doesn't interepret them as class selectors */
           var id = "#" + $(this).attr("id").replace(/(:|\.)/g,'\\$1');
           var x = $(this).offset().left - $(document).scrollLeft();
           var y = $(this).offset().top - $(document).scrollTop();
           var $description = $(id + " > .help-description");
           var title = $description.attr("title");
           var text = $description.html();
           $("#help-dialog").html(text);
           $("#help-dialog").dialog("option",{title: title, position: [x,y], height: 200, width: 400}).dialog("open");
           return false;
        });

        /* add and remove formsets (and forms) */

        $("button.add").button({
            icons: { primary : "ui-icon-circle-plus" },
            text: true
        }).click(function(event) {
            if ($(event.target).hasClass("FORM")) {
                var form = $(event.target).closest(".coolfieldset-content").find(".form:first");
                add_form(form);

            }
            else if ($(event.target).hasClass("FORMSET")) {
                var dynamic_formset_add_button = $(event.target).parent(".add_details").prev(".accordion").children(".add-row:last");
                $(dynamic_formset_add_button).click();
            }

        });

        $("button.remove").button({
            icons: { primary : "ui-icon-circle-minus" },
            text: true
        }).click(function(event) {
            var dynamic_formset_remove_button = $(event.target).closest(".accordion-content").next(".delete-row:first");

            $("#remove-dialog").html("\
                <p>Are you sure you wish to remove this item?</p>\
                <p><i>This will not delete it from the database; It will only remove its relationship to this model.</i></p>\
            ");
            $("#remove-dialog").dialog({
                modal       : true,
                dialogClass : "no-close",
                height      : 300,
                width       : 400,
                buttons : {
                    ok      : function() {
                        $("#remove-dialog").dialog("close");
                        $(dynamic_formset_remove_button).click();
                    },
                    cancel  : function() {
                        $("#remove-dialog").dialog("close");
                    }
                }
            }).dialog("open");

        });

        $("button#sort_vocabulary_up").button({
            icons: { primary : "ui-icon-arrowthick-1-n" },
            text: false
        });
        $("button#sort_vocabulary_down").button({
            icons: { primary : "ui-icon-arrowthick-1-s" },
            text: false
        });

        /* END enable fancy buttons */

        
        /* BEGIN enable accordions */

        /* (more accordion setup is done below) */

        $(".accordion").multiOpenAccordion({
            tabShown : function(event,ui) {
               var activeTab = ui["tab"];
               var activeContent = ui["content"];
               if ($(activeTab).hasClass("sorted")) {
                   /* if the accordion content is being opened just b/c it was clicked during sorting, then hide it and reset all relevant styles */
                   $(activeContent).hide();
                   $(activeTab).removeClass("sorted ui-state-active");
                   $(activeTab).addClass("ui-state-default");
                   var activeTabIcon = $(activeTab).find("span");
                   $(activeTabIcon).removeClass("ui-icon-triangle-1-s");
                   $(activeTabIcon).addClass("ui-icon-triangle-1-e");
               }
               else {
                   /* otherwise set a class to override the default open style (b/c it looks bad) */
                   $(activeTab).addClass("open-accordion");
               }
           },
           tabHidden : function(event,ui) {
               var activeTab = ui["tab"];
               $(activeTab).removeClass("open-accordion");
           },
           active : false   // this _should_ hide all panes, but there is a known bug [http://code.google.com/p/jquery-multi-open-accordion/issues/detail?id=15] preventing this
        });
        $(".ui-accordion-content").each(function() {
            $(this).hide(); // see comment about "active : false" above
        });

        /* END enable accordions */

        /* BEGIN enable containers */

        /* some of the container widgets can be selectively hidden and shown */
        /* if this javascript code is run while they are hidden, then it doesn't always get applied properly */
        /* so where possible I bind the widget's custom display event to initializeContainer */
        /* where that isn't possible, I just bind the regular show event to initializeContainer */
        /* (note that this is only possible b/c I redefined the show/hide fns in dcf_base.html) */

        // fieldsets...
        $(".coolfieldset").coolfieldset({
            speed   : "fast"
        });
// not bothering to call initializeContainer w/ fieldsets,
// since they won't have any content that needs initializing (that isn't a container itself)
//        $(".coolfieldset-content").bind("show", function() {
//           initializeContainer($(this));
//        });
//        // probably don't need the call above, since coolfieldsets are open by default, instead should use the call below
//        $(".coolfieldset-content").each(function() {
//            initializeContainer($(this));
//        });
        // btw, if I need to open/close a fieldset use the following code:
        // $(".coolfieldset[name='whatever'] legend").trigger("click");

        // accordions...
        // (more accordion setup is done both above and below)
        $(".accordion-content").bind("show",function() {
            initializeContainer($(this));
        });

        // tabs...
        $(".tabs").tabs({
            activate : function(event,ui) {
                initializeContainer(ui.newPanel);
            }
        });
       
        // panes...
        $(".pane").hide(); // hide panes unless they are explicitly activated by the treeview
        $(".pane").bind("show", function() {
            initializeContainer($(this));
        });

        /* END enable containers */

        /* BEGIN enable CUSTOMIZER-SPECIFIC things */

        if ($("#customize").length) {

            // tagging...
            $(".tags").tagit({
               allowSpaces : true,
               singleField : true,
               singleFieldDelimiter : "|",
               afterTagAdded : function(event,ui) {
                   var new_tag       = ui.tag
                   var new_tag_name  = $(new_tag).find(".tagit-label").text();
                   var new_tag_key   = new_tag_name.toLowerCase().replace(/ /g,'');
                   var new_tag_type  = $(new_tag).closest(".tagit").prev(".tags").attr("name");

                   var was_just_added = ($(new_tag).attr("class").indexOf("added") != -1);

                   if (new_tag_type == "standard_categories_tags") {
                       /* standard_categories_tags cannot be deleted */
                       $(new_tag).find(".tagit-close").hide();
                   }
                   else {
                      /* scientific_categories_tags can be edited */
                      $(new_tag).find(".tagit-label").before(
                        "<a class='tagit-edit' onclick='edit_tag(this);'><span class='ui-icon ui-icon-pencil'></span></a>"
                      );

                      if (was_just_added) {
                           $(new_tag).closest(".tab_content").find(".field_value[name='category'] select").each(function() {
                              var new_option = new Option(new_tag_key,new_tag_name);
                              $(this).append(new_option);
                          });
                      }

                   }
               },
               beforeTagRemoved : function(event,ui) {
                   var old_tag = ui.tag;
                   var old_tag_name  = $(old_tag).find(".tagit-label").text();
                   var old_tag_key   = old_tag_name.toLowerCase().replace(/ /g,'');
                   var old_tag_type  = $(old_tag).closest(".tagit").prev(".tags").attr("name");

                   // have to set this 1st, before the tag is removed
                   var category_selects = $(old_tag).closest(".tab_content").find(".field_value[name='category'] select")

                   if (old_tag_type.indexOf("scientific_categories_tags") !== -1) {
                       categories = SCIENTIFIC_CATEGORIES;
                       old_tag_component = old_tag_type.substr(0, old_tag_type.indexOf("_scientific_categories_tags"));
                   }
                   else {
                       categories = STANDARD_CATEGORIES;
                       alert("You shouldn't be deleting standard categories.  You're a very naughty boy.")
                   }

                   $("#confirm-dialog").html("Any properties belonging to this category will become uncategorized.  Are you sure you wish to continue?");
                   $("#confirm-dialog").dialog("option",{
                       title : "Delete Category?",
                       height : 200,
                       width  : 400,
                       buttons: {
                           ok : function() {
                               var category_to_delete = "";
                               $.each(categories,function(i,category) {
                                   var category_fields = category.fields
                                   if ((category_fields.key == old_tag_key) && (category_fields.component_name == old_tag_component)) {
                                     category_to_delete = category;
                                   }
                               });
                               category_to_delete.fields.remove = "True"

                               $(category_selects).each(function() {
                                   var selector = "option:contains(" + old_tag_name + ")";
                                   $(this).find(selector).remove();
                                   $(this).trigger("change");
                               });

                               $(this).dialog("close");
                           },
                           cancel : function() {
                               // the tag data is still in categories; just put it back in the widget
                               var tag_widget = $(event.target);
                               $(tag_widget).tagit("createTag",old_tag_name);
                               $(this).dialog("close");
                           }
                       }
                   }).dialog("open");
               }

            });
            $(".tagit-label").each(function() {
                $(this).attr("title","click to toggle attributes of this category");
            });
            $(".tagit").sortable({
                axis : "x",
                items : "li:not(.tagit-new)",
                placeholder : "sortable-item",
                stop : function( event, ui ) {
                    var sorted_tag = ui["item"];
                    var sorted_tags = $(sorted_tag).closest("ul.tagit").find("li.tagit-choice");
                    var ordered_tag_list = $(sorted_tags).map(function() {
                        return $(this).find(".tagit-label").text();
                    }).get().join("|");
                    var tag_type = $(sorted_tag).closest(".tagit").prev(".tags").attr("name");
                    order_categories(tag_type,ordered_tag_list);
                }
            });

            $(".tagit-choice").click(function(event){
                // if you really clicked the tag, and not an icon/button on the tag...
                if ($(event.target).attr("class").indexOf("ui-icon") == -1) {
                    // toggle its state..
                    $(this).toggleClass("ui-state-active");
                    var tag_label = $(this).find(".tagit-label").text();
                    // and that of all corresonding properties...
                    $(this).closest(".tab_content").find(".accordion-header .label[name$='category']").each(function() {
                        //alert("does " + $(this).text() " == " + )
                        if ($(this).text()==tag_label) {
                            var section = $(this).closest(".sortable-item");    // this is the accordion (recall it's wrapped in a div to enable sorting)
                            $(section).toggle();
                        }
                    });
              }
            });
            /* I'm using separate widget to add tags, so disable the .tagit-new box */
            $(".tagit-new").attr("style","display:none!important;");
            /* and enable this widget */
            $("[id$='_scientific_categories_tags_add']").keypress(function(e) {
                if(e.which == 13) {
                    var input = $(e.target)
                    var tag_name = $(input).val();
                    var tag_widget = $(input).closest(".tab_content").find(".tags");
                    if ($(tag_widget).tagit("createTag",tag_name,"added")) {
                        $(input).val("");
                        $(tag_widget).next(".tagit:first").find(".tagit-choice").each(function(i,new_tag) {
                            // TODO: THIS SEEMS PRETTY SLOW, SEARCHING THROUGH EVERY TAG
                            var new_tag_name  = $(new_tag).find(".tagit-label").text();
                            var new_tag_key   = new_tag_name.toLowerCase().replace(/ /g,'');
                            var new_tag_type  = $(new_tag).closest(".tagit").prev(".tags").attr("name");
                            var new_tag_component_name = $(new_tag).closest(".tab_content").attr("name");

                            if ( ! isTagInCategories(new_tag_key,new_tag_component_name,SCIENTIFIC_CATEGORIES)) {

                                var new_category = {
                                    "pk": 0,
                                    "model": "dcf.metadatascientificcategory",
                                    "fields": {
                                        "name": new_tag_name,
                                        "vocabulary": 0,
                                        "description": "",
                                        "project": 0,
                                        "key": new_tag_key,
                                        "component_name": new_tag_component_name,
                                        "order": i,
                                        "remove": false
                                    }
                                }
                                SCIENTIFIC_CATEGORIES.push(new_category);
                            }
                            else {
                                // this handles the rare case where you are adding something that was previously removed in this session
                                $.each(SCIENTIFIC_CATEGORIES,function(i,category) {
                                    category_fields = category.fields;
                                    if ((category_fields.key==new_tag_key) && (category_fields.component_name == new_tag_component_name)) {
                                        category.fields.remove = false;
                                    }
                                });
                            }
                        });
                    }
                    e.preventDefault();
                    return false;
                }
            });

            /* enable sortable multi-open accordions in the customizer */
            $("#customize .accordion").find(".accordion-header").each(function() {
                /* first wrap each accordion header & content pair in a div */
                /* b/c the sortable items need to be a single unit */
                var accordion_unit = "<div class='sortable-item'></div>";
                $(this).next().andSelf().wrapAll(accordion_unit);
            });
            $("#customize .accordion").sortable({
                axis : "y",
                handle : "h3",
                placeholder : "sortable-accordion-placeholder",
                stop : function( event, ui ) {
                    /* after sorting tag the sorted item so that I can cancel the open accordion event */
                    var sortedItem = ui["item"];
                    var sortedTab = $(sortedItem).find(".accordion-header");
                    $(sortedTab).addClass("sorted")
                    /* and re-calculate each field's order */
                    $(sortedTab).closest(".accordion").find(".accordion-content").each(function(i) {
                        var order_input = $(this).find("input[name$='-order']");
                        $(order_input).val(i+1);
                        $(order_input).trigger("change");
                    });
                }
                // TODO: jquery documentation implies some more code here to handle IE bug
            });

            /* enable the customize-subform button */
            $("button.customize-subform").button({
                icons : { primary : "ui-icon-extlink"}
            });
            // force the change event to hide/show the customize-subform button as appropriate
            $(".field_value[name='customize_subform']").find("input").trigger("change");

        }

        /* END enable CUSTOMIZER-SPECIFIC things */

        /* BEGIN enable EDITOR-SPECIFIC things */

        if ($("#edit").length) {

            /* wrap multi-accordions in a div */
            /* (so that I can add/delete them dynamically as a unit */
            $("#edit .accordion:not(.scientific_properties)").find(".accordion-header").each(function() {
                var prefix = $(this).closest(".accordion").attr("prefix");
                var accordion_unit = "<div class='subform' prefix='" + prefix + "'></div>";
                $(this).next().andSelf().wrapAll(accordion_unit);
            });


            /* dockable splitter */
            /* TODO: THIS IS NOT CURRENTLY USED */
            $("#splitter").splitter({
                minAsize:100,
                maxAsize:400,
                splitVertical:true,
                A:$('#splitter_left'),
                B:$('#splitter_right'),
                closeableto: 1 // default is 0, but that causes dropped float bug
            });

            /* fancy treeview */
            $.ui.dynatree.nodedatadefaults["icon"] = false; // Turn off icons by default
            $(".tree").dynatree({
                debugLevel      : 0,
                checkbox        : true,
                selectMode      : 3,
                minExpandLevel  : 1,
                onActivate      : function(node) {
                    active_pane_name = node.data.title.toLowerCase() + "_pane";
                    active_pane = $("#"+active_pane_name);
                    $(active_pane).show();
                    $(active_pane).toggleClass("active_pane");
                    $(active_pane).find(".tabs:first").tabs({"active" : PREVIOUSLY_SELECTED_TAB})
                },
                onDeactivate    : function(node) {
                    inactive_pane_name = node.data.title.toLowerCase() + "_pane";
                    inactive_pane = $("#"+inactive_pane_name);
                    PREVIOUSLY_SELECTED_TAB = $(inactive_pane).find(".tabs:first").tabs("option","active");
                    $(inactive_pane).hide();
                    $(inactive_pane).toggleClass("active_pane");
                },
                onSelect        : function(flag,node) {
                    selected_nodes = $(".tree").dynatree("getSelectedNodes");
                    $(".dynatree-partsel:not(.dynatree-selected").each(function() {
                        var node = $.ui.dynatree.getNode(this);
                        selected_nodes.push(node);
                    });
                    node.tree.visit(function(node){
                       var pane = $("#"+node.data.title.toLowerCase()+"_pane");
                       if ($.inArray(node,selected_nodes)>-1) {
                            $(pane).find("input[name$='-active']").attr("checked",true);
                            $(pane).removeClass("ui-state-disabled");
                       }
                       else {
                            $(pane).find("input[name$='-active']").attr("checked",false);
                            $(pane).addClass("ui-state-disabled");
                       }
                    });
                }
            });
            $(".tree").each(function() {
                var root = $(this).dynatree("getRoot");
                root.visit(function(node) {
                    node.select(true);  // TODO: this is selecting everything by default; it should get select status from python
                    node.expand(true);
                });
                var first_child = root.getChildren()[0];
                first_child.activate(true);
            });

        }

        /* END enable EDITOR-SPECIFIC things */

        /* BEGIN enable misc widgets */

        /* some widgets' functionality aren't dependent on being visible
         * so I can initialize them here and just be done with it
         */

        /* enable autocompletion */
        $(".autocomplete").each(function(){
            var suggestions = $(this).attr("suggestions").split("|");
            $(this).autocomplete({
                source : suggestions
            });
        });

        /* enable calendar widgets */
        $(".datepicker").datepicker({
            changeYear : true,
            showButtonPanel : false,
            showOn : 'button'
        }).next("button").button({
            icons : {
                primary : "ui-icon-calendar"
            },
            text : false
        });
        $(".ui-datepicker-trigger").mouseover(function() {
            $(this).css('cursor', 'pointer');
        });
        $(".ui-datepicker-trigger").attr("title","click to select date");

        /* END enable misc widgets */


        INITIALIZED = 1;
        
        /* BEGIN render any errors */

        //FUNCTION_QUEUE.dequeue("errors");

        $(".error-wrapper").each(function() {
           render_error($(this));
        });

        /* END render any errors */

    })

};

function initializeContainer(container) {

    if (! $(container).hasClass("initialized")) {



        /* change the look and feel of a disabled field */
        /* sets the "readonly" class on that field's label & the actual field */
        /* CSS does the rest */
        $(container).find(".readonly:not(.readonly-initialized)").each(function() {
            // works for fields in a table (tr) or a div
            $(this).closest("tr.field,div.field").find(".field_label,.field_value").addClass("readonly");
            $(this).addClass("readonly-initialized");
        });

        /* enumerations */
        $(container).find(".enumeration-other:not(.enumeration-other-initialized)").change(function() {
            var DEFAULT_OTHER_TEXT = "please enter custom selection (or else de-selected '--OTHER' above)";
            var value = $(this).val().replace(/\s+/g,'');
            if (! value) {
                $(this).val(DEFAULT_OTHER_TEXT);
            }
        });
        /*
        $(container).find(".enumeration-value:not(.enumeration-value-initialized)").each(function() {
            // hide enumeration-other (will be overwritten if "--OTHER--" is selected below)
            var enumeration_other = $(this).siblings(".enumeration-other:first");
            $(enumeration_other).hide();
            $(this).addClass("enumeration-value-initialized");
        });
        */
        $(container).find(".enumeration-other:not(.enumeration-other-initialized").each(function() {
            $(this).before("<br/>");
            // hide enumeration-other (will be overwritten if "--OTHER--" is selected below)
            $(this).hide();
            $(this).addClass("enumeration-other-initialized");
        });


        /* combo-boxes w/ checkboxes & radioboxes */
        $(container).find(".multiselect:not(.multiselect-initialized)").multiselect({
            autoOpen    : false,
            minWidth    : 500,
            create      : function(event,ui) {

                var enumeration_value = $(event.target);
                var enumeration_other = $(enumeration_value).siblings(".enumeration-other:first");

                var values = $(enumeration_value).multiselect("getChecked").map(function() {
                    return this.value;
                }).get();

                if (values.indexOf("OTHER") != -1) {
                    // if "--OTHER--" is selected, then show enumeration-other
                    $(enumeration_other).width($(enumeratio_value).siblings(".ui-multiselect:first").width());
                    $(enumeration_other).show();
                }
                else {
                    $(enumeration_other).hide();
                }

                if (values.indexOf("NONE") != -1) {
                    // if "--NONE--" is slected, then de-select everything else
                    $(enumeration_value).multiselect("getChecked").each(function() {
                        if (this.value != "NONE") {
                            this.click();
                        }
                    });
                    $(enumeration_other).hide();
                }

                // sometimes these lists have an onchange event
                // force the event callback to run upon initialization
                $(this).trigger("change");

            },
            close       : function(event,ui) {

                var enumeration_value = $(event.target);
                var enumeration_other = $(enumeration_value).siblings(".enumeration-other:first");

                var values = $(enumeration_value).multiselect("getChecked").map(function() {
                    return this.value;
                }).get();

                if (values.indexOf("OTHER") != -1) {
                    // if "--OTHER--" is selected, then show enumeration-other
                    $(enumeration_other).width($(enumeration_value).siblings(".ui-multiselect:first").width());
                    $(enumeration_other).show();
                }
                else {
                    $(enumeration_other).hide();
                }

                if (values.indexOf("NONE") != -1) {
                    // if "--NONE--" is slected, then de-select everything else
                    $(enumeration_value).multiselect("getChecked").map(function() {
                        if (this.value != "NONE") {
                            this.click();
                        }
                    })
                    $(enumeration_other).hide();
                }
            }
        })
        $(container).find(".multiselect[multiple]:not(.multiselect-initialized)").multiselect({
            noneSelectedText    : "please enter selections",
            selectedText        : function(numChecked, numTotal, checkedItems) {
                if ($("#customize").length) {
                    return numChecked + ' of ' + numTotal + ' selected ';
                }
                MAX_LENGTH = 40;
                if (numChecked > 0) {
                    text = "\"" + checkedItems[0].value.substr(0,MAX_LENGTH);
                    if (checkedItems[0].length >= MAX_LENGTH) {
                        text += "...\"";
                    }
                    else {
                        text += "\"";
                    }
                    if (numChecked > 1) {
                        text += "  + " + (numChecked-1) + " more selections"
                    }
                    return text;
                }
            },
            header              : true
        });
        $(container).find(".multiselect:not([multiple]):not(.multiselect-initialized)").multiselect({
            noneSelectedText    : "please enter selection",
            selectedList        : 1,
            multiple            : false,
            header              : false,
            // these next 2 handlers extend the plugin so that de-selecting an option in singl emode causes noneSelectedText to be shown
            open                : function(event,ui) {
                $(event.target).attr("previous_selection",$(event.target).val());
            },
            click               : function(event,ui) {
                if ($(event.target).attr("previous_selection") == ui.value) {
                    $(event.target).multiselect("uncheckAll");
                }
            }
        });
        $(container).find(".multiselect").addClass("multiselect-initialized");


        /* deal w/ dynamic formsets */

        //$(container).find(".accordion:not(.scientific_properties):not(.formset-initialized)").each(function() {
        $(container).find(".subform:not(.formset-initialized)").each(function() {
            if ($(this).is(":visible")) {
            var prefixes = $(this).parents(".subform").map(function() {
                return $(this).attr("prefix");
            }).get().join("-");
                var prefix = $(this).attr("prefix");
                
                $(this).formset({
                    prefix          : prefix,
                    formCssClass    : prefix + "_subform",
                    added           : function(row) {
                        add_formset(row);
                    }
                })
                $(this).addClass("formset-initialized")
            }
        });

        $(container).addClass("initialized");
    }
}


function order_categories(category_type,ordered_categories) {
    if (category_type=="standard_categories_tags") {
        categories = STANDARD_CATEGORIES;
    }
    else {
        categories = SCIENTIFIC_CATEGORIES;
    }
    ordered_categories_list = ordered_categories.split("|");
    for (var i=0; i<ordered_categories_list.length; i++) {
        category_name = ordered_categories_list[i];
        category_key  = category_name.toLowerCase().replace(/ /g,'');
        $.each(categories, function(j,v) {
            if (v.fields.key == category_key) {
                v.fields.order = i
                return false;
            }
        });
    }
};


/* display an error in the correct location
 * also, color any containing tabs or accordions */
function render_error(error) {

    // render fieldsets...
    $(error).parents(".coolfieldset").each(function() {
        // (doing this manually (w/ CSS) instead of via JQuery's built-in UI system)
        // (b/c it would indicate that _everything_ in the fieldset is in error)'
        $(this).addClass("error");
    });
    // render accordions...
    $(error).parents(".accordion-content").each(function() {
        $(this).prev(".accordion-header").addClass("ui-state-error");
    });
    // render tabs...
    $(error).parents(".tab_content").each(function() {
        var tab_id = $(this).parent().attr("id");
        $("a[href='#"+tab_id+"']").closest("li").addClass("ui-state-error");
    });
    // render treeview nodes...
    var pane_name = $(error).closest(".pane").attr("name");
    $("#component_tree .dynatree-title").each(function() {
       if ($(this).text().toLowerCase() == pane_name) {
           $(this).addClass("error");   // as above doing this via CSS instead of JQuery
       }
    });
};

function render_msg(parent) {
   /* if a msg exists, then display it */
    var msg = $(parent).find("#msg").text().trim();
    if (msg && msg.length) {
        $(parent).find("#msg").dialog({
            modal : true,
            hide : "explode",
            height : 150,
            width : 350,
            // no longer able to set this in JQuery UI > 10.3
            //title: "<span class='ui-icon ui-icon-notice'></span>",
            buttons: {
                OK: function() {
                    $(this).dialog("close");
                }
            }
        });
    }
};


function sort_accordions(accordions,key) {

    if (key.indexOf("name")>=0) {
        key_selector = "span[name='property_name']";
    }
    else if (key.indexOf("category")>=0) {
       key_selector = "span[name='property_category']";
    }
    else if (key.indexOf("order")>=0) {
       key_selector = "span[name='property_order']";

    }
    else {
        alert("unknown sort key: "+key)
    }

    var sortable_items = $(accordions).children(".sortable-item").get();
    sortable_items.sort(function(a,b){

       var a_key = $(a).find(key_selector).text();
       var b_key = $(b).find(key_selector).text();
       if (key.indexOf("order")>=0) {
           a_key = parseInt(a_key);
           b_key = parseInt(b_key);
       }

       return (a_key < b_key) ? -1 : (a_key > b_key) ? 1 : 0;
    });

    $.each(sortable_items, function(i, item) {
        $(accordions).append(item);
    });

};


function set_label(item,label_name) {
    var selector = "span.label[name='"+label_name+"']"
    var label = $(item).closest(".accordion-content").prev(".accordion-header").find(selector);
    var input_type = $(item).prop("tagName").toLowerCase();
    if (input_type=="select") {
        var new_text = ($(item).val()) ? $(item).find("option:selected").text() : "None";
        if (new_text=="") {
            new_text = "None";
        }
        $(label).text( new_text );
    }
    else if (input_type=="input") {
        var new_text = ($(item).val()) ? $(item).val() : "None";
        $(label).text( new_text );
    }

};


/* restricts the set of options of a set of target fields
 * to the selected options of the source field
 * (targets must be in the same form/subform)
 */
function restrict_options(source,targets) {
    var restrictions = [];
    $(source).find("option:selected").each(function() {
        restrictions.push($(this).val());
    });

    for (var i=0; i<targets.length; i++) {
        var selector = "*[name$='" + targets[i] + "']";
        var target = $(source).closest(".form").find(selector).find("select");
        var options = [];
        $(target).find("option").each(function() {
            options.push($(this).val());
        });
       
        // (this is horrible syntax; "grep" doesn't mean the same thing in JQuery)
        var in_options_but_not_restrictions = $.grep(options,function(el){
           return $.inArray(el,restrictions) == -1;
        });
        var in_restrictions_but_not_options = $.grep(restrictions,function(el){
           return $.inArray(el,options) == -1;
        });

        // remove everything in options and not in restrictions
        $(in_options_but_not_restrictions).each(function() {
            $(target).find("option[value='"+this+"']").remove();
        });
        // add everything in restrictions and not in options
        $(in_restrictions_but_not_options).each(function() {
            var option = $(source).find("option[value='"+this+"']");
            $(target).append($("<option>").attr("value",this).text($(option).text()));

        });

        // refresh the multiselect widget if needed
        if ($(target).hasClass("multiselect")) {
            $(target).multiselect("refresh");
        };
    }
};


/* toggles the visibility of a set of target fields
 * based on the value of the source field
 * (targets must be in same form/subform)
 */
function enable(source,enablingValue,targets) {
    var sourceValueMatches = false;
    if ($(source).attr("type") == "checkbox") {
        if ( ( ( enablingValue.toLowerCase()=="true" ) && ( $(source).is(":checked") ) )  || ( ( enablingValue.toLowerCase()=="false" ) && !( $(source).is(":checked") ) ) ) {
            sourceValueMatches = true;
        }
    }
    else if ( ($(source).prop("tagName").toLowerCase()=="select") && ($(source).attr("multiple"))) {
        alert("I still need to write a handler in enable() for multiselects");
    }
    else {
        if ($(source).val() == enablingValue) {
            sourceValueMatches = true;
        }
    }

    for (var i = 0; i < targets.length; i++) {
        var selector = "*[name$='" + targets[i] + "']";
        var target = $(source).closest(".form").find(selector).filter("input,textarea,select,button");
        var targetType = $(target).prop("tagName").toLowerCase();

        if (targetType=="button") {
            if (sourceValueMatches) $(target).button("enable");
            else $(target).button("disable");
        }
        else if (targetType=="select") {
            if (sourceValueMatches) {
                $(target).unbind("focus");
                $(target).closest("tr.field").find(".field_label, .field_value").removeClass("readonly");
            }
            else {
                $(target).bind("focus",function() { $(this).blur(); })
                $(target).closest("tr.field").find(".field_label, .field_value").addClass("readonly");
            }
        }
        else { /* if ((targetType=="input") || (targetType=="textarea")) { */

            if (sourceValueMatches) {
                $(target).removeAttr("readonly");
                $(target).closest("tr.field").find(".field_label, .field_value").removeClass("readonly");
            }
            else {
                $(target).attr("readonly","readonly");
                $(target).closest("tr.field").find(".field_label, .field_value").addClass("readonly");
            }
        }
    }

};

/* used to check if a tag element exists in the categories dict */
function isTagInCategories(tag_key,tag_component_name,categories) {
    var found_tag = false;
    $.each(categories,function(i,category) {
        var category_fields = category.fields;
        if ((category_fields.key == tag_key) && (category_fields.component_name == tag_component_name)) {
            found_tag = true;
            return false;
        }
    });
    return found_tag;
}

/* takes the content of the global JSON variables and copies them back into hidden form fields */
function copy_categories() {    
    var standard_categories_content = $("#id_standard_categories_content");
    var scientific_categories_content = $("#id_scientific_categories_content");
    $(standard_categories_content).val(JSON.stringify(STANDARD_CATEGORIES));
    $(scientific_categories_content).val(JSON.stringify(SCIENTIFIC_CATEGORIES));
};


function customize_subform(button) {

    var field_name      = $(button).closest(".customize_subform_details").find(".field_name").text();
    var version_number  = $(button).closest(".customize_subform_details").find(".version_number").text();
    var project_name    = $(button).closest(".customize_subform_details").find(".project_name").text();
    var model_name      = $(button).closest(".customize_subform_details").find(".model_name").text();
    var customizer_name = $(button).closest(".customize_subform_details").find(".customizer_name").text();

    var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/customize_subform/";
    url += "?f=" + field_name + "&v=" + version_number + "&p=" + project_name + "&m=" + model_name + "&c=" + customizer_name;

    var customize_subform_dialog = $("<div></div>");
    $.ajax({
         url        : url,
         type       : "GET",
         cache      : false,
         success    : function(data) {
            var title = "Customizing " + project_name.toLowerCase() + "::" + model_name.toLowerCase() + "::" + field_name.toLowerCase()
            customize_subform_dialog.html(data);
            customize_subform_dialog.dialog({
                title : title,
                modal : true,
                dialogClass: "no-close",
                height : 600,
                width : 1000,
                open : function() {
                    // apply all of the JQuery code to _this_ dialog
                    enableDCF();
                    render_msg(customize_subform_dialog);
                },

                buttons : {
                    save : function() {
 
                        var subform_data = $(this).find("#customize_subform").serialize();
                        /* I don't have to worry about populating the current form w/ the result of this POST */
                        /* b/c the created customizer already has the same name/project/version so it will be found when needed */
                        $.ajax({
                            url     : url,
                            type    : "POST",   // (POST mimics submit)
                            data    : subform_data,
                            cache   : false,
                            success : function(data) {
                                if (data == "success") {
                                    $(customize_subform_dialog).dialog("close");
                                }
                                else {
                                    $(customize_subform_dialog).html(data);
                                    render_msg(customize_subform_dialog); // unlike the main forms, subforms have to explicitly call render_msg b/c they don't get re-opened on submit, the content just gets refreshed
                                }
                            },
                            error   : function(xhr,status,error) {
                               console.log(xhr.responseText + status + error);
                            }

                        })
                    },
                    cancel : function() {
                        $(customize_subform_dialog).dialog("close");
                    }
                },
                close   : function() {
                    $(this).dialog("destroy");
                }
            }).dialog('open');
         }
     })

};

function edit_tag(edit_tag_icon) {
    var tag_name = $(edit_tag_icon).next(".tagit-label").text();
    var tag_key  = tag_name.toLowerCase().replace(/ /g,'');
    var tag_type = $(edit_tag_icon).closest(".tagit").prev(".tags").attr("name");
    if (tag_type.indexOf("scientific_categories_tags") !== -1) {
        categories = SCIENTIFIC_CATEGORIES;
        tag_component = tag_type.substr(0, tag_type.indexOf("_scientific_categories_tags"));
    }
    else {
        categories = STANDARD_CATEGORIES;
        alert("You shouldn't be editing standard categories.  You're a very naughty boy.")
    }

    var category_to_edit = "";
    $.each(categories,function(i,category) {
       var category_fields = category.fields
       if ((category_fields.key == tag_key) && (category_fields.component_name == tag_component)) {
           category_to_edit = category;
           
       }
    });

    var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/customize_category/";
    url += "?k=" + category_to_edit.fields.key + 
           "&c=" + category_to_edit.fields.component_name +
           "&n=" + category_to_edit.fields.name +
           "&d=" + category_to_edit.fields.description +
           "&o=" + category_to_edit.fields.order

    var data = category_to_edit;
    var category_dialog = $("<div></div>");
    $.ajax({
         url        : url,
         type       : "GET",
         cache      : false,
         success    : function(data) {
            var title = "";
            category_dialog.html(data);
            category_dialog.dialog({
                title : title,
                modal : true,
                dialogClass: "no-close",
                height : 400,
                width : 600,
                open : function() {
                    // apply all of the JQuery code to _this_ dialog
                    enableDCF();
                },

                buttons : {
                    ok : function() {
                        form_data = $(this).find("#category_form").serializeArray();
                        for (var i=0; i<form_data.length; i++) {
                            field_data = form_data[i];
                            category_to_edit.fields[field_data.name] = field_data.value;
                        }
                        $(category_dialog).dialog("close");
                    },
                    cancel : function() {
                        $(category_dialog).dialog("close");
                    }
                },
                close   : function() {
                    $(this).dialog("destroy");
                }
            }).dialog('open');
         }
     })
};






 function getCookie(c_name)
    {
        if (document.cookie.length > 0)
        {
            c_start = document.cookie.indexOf(c_name + "=");
            if (c_start != -1)
            {
                c_start = c_start + c_name.length + 1;
                c_end = document.cookie.indexOf(";", c_start);
                if (c_end == -1) c_end = document.cookie.length;
                return unescape(document.cookie.substring(c_start,c_end));
            }
        }
        return "";
     }




function add_form(form) {
    var add_details = $(form).next(".add_details");
    
    var version_number  = $(add_details).find(".version_number").text();
    var project_name    = $(add_details).find(".project_name").text();
    var customizer_name = $(add_details).find(".customizer_name").text();
    var model_name      = $(add_details).find(".model_name").text();
    var field_name      = $(add_details).find(".field_name").text();

    var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/add_submodel";
    url += "?v=" + version_number + "&p=" + project_name + "&c=" + customizer_name + "&m=" + model_name + "&f=" + field_name;

    $.ajax({
        url     : url,
        type    : "GET",
        cache   : false,
        success : function(data) {
            $("#add-dialog").html(data);
            $("#add-dialog").dialog({
                modal       : true,
                dialogClass : "no-close",
                height      : 400,
                width       : 400,
                open        : function() {
                    // calling this causes the splitter to be re-created
                    // a good solution would be to check if it's initialized first
                    // but since the add_model form doesn't rely on JQuery,
                    // I've just commented it out
                    // enableDCF();
                },
                buttons : {
                    ok      : function() {
                        alert("you clicked ok");
                        $("#add-dialog").dialog("close");
                    },
                    cancel  : function() {
                        $("#add-dialog").dialog("close");
                    }
                }
            }).dialog("open");
        }
    });

}

function add_formset(row) {

    var form_to_add = $(row).find(".form:first")
    
    var add_details = $(row).closest(".accordion").next(".add_details");

    var version_number  = $(add_details).find(".version_number").text();
    var project_name    = $(add_details).find(".project_name").text();
    var customizer_name = $(add_details).find(".customizer_name").text();
    var model_name      = $(add_details).find(".model_name").text();
    var model_id        = $(add_details).find(".model_id").text();
    var field_name      = $(add_details).find(".field_name").text();

    var min      = $(add_details).find(".min").text();
    var max      = $(add_details).find(".max").text();

    var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/add_submodel";
    url += "?v=" + version_number + "&p=" + project_name + "&c=" + customizer_name + "&m=" + model_name + "&f=" + field_name + "&i=" + model_id;
  
    $.ajax({
        url     : url,
        type    : "GET",
        cache   : false,
        success : function(data) {
            $("#add-dialog").html(data);
            $("#add-dialog").dialog({
                modal       : true,
                dialogClass : "no-close",
                height      : 400,
                width       : 400,
                open        : function() {
                    // calling this causes the splitter to be re-created
                    // a good solution would be to check if it's initialized first
                    // but since the add_model form doesn't rely on JQuery,
                    // I've just commented it out
                    // enableDCF();
                },
                buttons : {
                    ok      : function() {

                        var id_to_add = $(this).find("select").val();
                        var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/get_submodel";
                        url += "?v=" + version_number + "&p=" + project_name + "&c=" + customizer_name + "&m=" + model_name + "&f=" + field_name + "&i=" + id_to_add;
                        $.ajax({
                            url     :    url,
                            type        : "GET",
                            cache       : false,
                            dataType    : "json",
                            success : function(data) {
                                //populate($.parseJSON(data),form_to_add);
                                populate(data[0],form_to_add);
                                update_formset(form_to_add);
                            },
                            error   : function(xhr,status,error) {
                               console.log("AJAX ERROR: " + xhr.responseText + " " + status + " " + error);
                            }
                        });

                        $("#add-dialog").dialog("close");
                    },
                    cancel  : function() {
                        $("#add-dialog").dialog("close");
                    }
                }
            }).dialog("open");
        },
        error   : function(xhr,status,error) {
            console.log("AJAX ERROR: " + xhr.responseText + " " + status + " " + error);
        }
    });
    
}

function populate(data, form) {
    $.each(data,function(key,value) {
        if (key=="pk") {
            var pk_input=$(form).find("input[name$='-pk']");
            $(pk_input).val(value);
        }
        if (key=="fields") {
            for (key in value) {
                if (value.hasOwnProperty(key)) {
                    // match all elements with the name of the key (that are children of field)
                    
                    var field_selector  = "*[name$='-"+key+"'],[name$='-"+key+"_0']";
                    var field           = $(form).find(field_selector);
                    if ($(field).length) {

                        var field_type      = $(field).prop("tagName").toLowerCase();                                         
                    
                        // field can either be input, select (single or multi), or subform (form or formset)
                        if (field_type == "input") {
                            $(field).val(value[key]);                        
                        }
                        else if (field_type == "select") {
                            if ($(field).filter("[multiple='multiple']")) {                                
                                var field_value = String(value[key]).split("||");
                                var enumeration_value = field_value[0].split("|");
                                var enumeration_other = field_value[1];
                                $(field).val(enumeration_value)
                                $(form).find("*[name$='-"+key+"_1']").val(enumeration_other);

                            }
                            else {
                                var field_value = String(value[key]).split("|");
                                var enumeration_value = field_value[0];
                                var enumeration_other = field_value[1];
                                $(field).val(enumeration_value);
                                $(form).find("*[name$='-"+key+"_1']").val(enumeration_other);
                            }
                        }
                        else {
                            alert(key + " is a relationship")
                        }
                    }
                }
            }
        }
    });
}

function update_formset(form) {
    // cloninig a formset (using django-dynamic-forms) just copies the structure exactly
    // this means that the prefixes of any nested formsets will be exactly the same as what already existed
    // this means that there will be naming conflicts (and a managementform error) in django when I try to save the forms
    // so this updates the prefixes
    $(form).find("*[prefix]").each(function() {
        alert($(this).attr("prefix"));
    });
}

function inherit(item) {
    var inherited_options = $(item).next();    
    if ($(inherited_options).find(".enable_inheritance").is(":checked")) {
        var item_name = $(item).attr("name");
        var active_pane_name = $(item).closest(".active_pane").attr("name").toLowerCase();
        var child_panes = $("#component_tree li#" + active_pane_name).find("li");
        if ($(item).attr("type") == "checkbox") {
            // checkbox
            var item_value = $(item).is(":checked");
            $(child_panes).each(function() {
                var child_pane_name = $(this).attr("id");
                var child_item_name = child_pane_name + "-" + item_name.substring(item_name.indexOf('-')+1);
                var child_item = $("input[name='"+child_item_name+"']");
                if ($(child_item).next().find(".enable_inheritance").is(":checked")) {
                    $(child_item).prop("checked",item_value);
                }
            });
        }
        else if ($(item).prop("tagName").toLowerCase()=="select") {
                if ($(source).attr("multiple")) {
                    // multiple select

                }
                else {
                    // single select
                    var item_value = $(item).val();
                    //var other_value = $(item)
                    $(child_panes).each(function() {
                        var child_pane_name = $(this).attr("id");
                        var child_item_name = child_pane_name + "-" + item_name.substring(item_name.indexOf('-')+1);
                        var child_item = $("select[name='"+child_item_name+"']");
                        if ($(child_item).next().find(".enable_inheritance").is(":checked")) {
                            $(child_item).val(item_value);
                        }
                    });
                }
        }
        else {
            // text input or textarea
            var item_value = $(item).val();
            $(child_panes).each(function() {
                var child_pane_name = $(this).attr("id");
                var child_item_name = child_pane_name + "-" + item_name.substring(item_name.indexOf('-')+1);
                var child_item = $("input[name='"+child_item_name+"'],textarea[name='"+child_item_name+"']");
                if ($(child_item).next().find(".enable_inheritance").is(":checked")) {
                    $(child_item).val(item_value);
                }
            });
        }
    }
};

function move_option_up(select_id) {
    var select = $("select[id='"+select_id+"']");
    $(select).find(":selected").each(function(i,option) {
        if (!$(this).prev().length) return false;
        $(this).insertBefore($(this).prev());
    });
//    $(select).focus().blur();
};


function move_option_down(select_id) {
    var select = $("select[id='"+select_id+"']");
    $($(select).find(":selected").get().reverse()).each(function(i,option) {
        if (!$(this).next().length) return false;
        $(this).insertAfter($(this).next());
    });
//    $(select).focus().blur();
}
