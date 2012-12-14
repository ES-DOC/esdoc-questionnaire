/* dictionary of current categories */
/* each category key contains a dictionary representing the JSON serialization of the category */
/* note that to access the values of that dictionary in comparisons, you have to use .toString() */
var categories = {}

/* a simple helper function that lets me inspect the above dictionary */
function dictionarySize(dict) {
    var size = 0;
    for (var key in dict) {
        if (dict.hasOwnProperty(key)) size++;
    }
    return size;
};

/* a useful way to print out the above dictionary is:
 * JSON.stringify
 */

/* returns a Django Form serialized into the specified format
 * (currently only JSON is supported; can't think why I'd need another format */
function serializeForm(form,format) {
    if(format.toLowerCase()=='json') {
        var data = {};
        $.each(form.serializeArray(), function() {
            data[this.name] = this.value;
        });
        return data;
    }
    else {
        alert("invalid serialization format");
    }
};

/* initially, a lot of the form elements are hidden */
/* (inside accordions or behind inactive tabs) */
/* so this fn gets called whenever a new section is displayed */
/* it winds up repeating some of the functionality of enableJQueryWidgets below */
function initializeSection(parent) {
    alert("initialize");
};

function initializeTag(tag) {
    var tagName = $(tag).find(".tagit-label").text();
    var tagKey = tagName.replace(/ /g,'');
    var category = categories[tagKey];
    var categoryID = category["pk"];

    var isDefaultCategory = category["_isDefault"].toString()=="true"

    /* no-matter whether tag is default or not,
     * add the show button */
    $(tag).find(".tagit-label").before(
        "<input type='checkbox' class='tagit-show' id='tagit-show-"+categoryID+"'/><label class='tagit-show-label' for='tagit-show-"+categoryID+"'>toggle the display of these fields</label>&nbsp;"
    );
    
    /* if the tag is not the default tag for this model, 
     * go ahead and add the edit icon */
    if (!isDefaultCategory) {
        $(tag).find(".tagit-label").before(
            "<a class='tagit-edit' onclick='editTag(this);'><span class='ui-icon ui-icon-pencil'></span></a>"
        );
    }

    /* if the tag is the default tag for this model,
     * disable the close icon */
    if (isDefaultCategory) {
        $(tag).find(".tagit-close").hide();
    }

    
};

/* the order of tags is handled implicitly by the tagit plugin
 * but this fn copies that order to the data in the categories dictionary
 */
function reorderTags() {
    var currentTags = $("#field-types").val().split("|");
    for (var i=0; i < currentTags.length; i++) {
        tagName = currentTags[i];
        tagKey = tagName.replace(/ /g,'');
        if (categories.hasOwnProperty(tagKey)) {
            categories[tagKey].order = i
        }
        //categories[tagKey].order = i;
    }
};


/*
 * fn called when the show tag icon is clicked
 */
function showTag(tag_icon) {

};

/*
 * fn called when the edit tag icon is clicked
 */
function editTag(tag_icon) {

   var tagName = $(tag_icon).next(".tagit-label").text();
   var tagKey = tagName.replace(/ /g,'');
   var tag = categories[tagKey];

   var url = window.document.location.protocol + "//" + window.document.location.host + "/metadata/ajax/edit_field_category";
   url += "?i=" + tag.pk;
   for (var key in tag) {
       if (tag.hasOwnProperty(key)) {
           url += "&" + key + "=" + tag[key]
       }
   }
   
   $.ajax({
        url : url,
        success : function(data) {
            var title = "edit field category: " + tagName;
            $("#edit-dialog").html(data);
            $("#edit-dialog").dialog("option",{
                title : title,
                height: 300,
                width: 700,
                buttons : {
                    ok : function() {
                        var data = serializeForm($(this).find("form"),"JSON");
                        for (var key in data) {
                            tag[key] = data[key]
                        }
                        $(this).dialog("close");
                    },
                    cancel : function() {
                        $(this).dialog("close");
                    }
                }

            }).dialog("open");
        }
    })



};

function setLabel(item) {
    var label = $(item).closest(".accordion-content").prev(".accordion-header").find("span.label");
    var newText = ($(item).val()) ? $(item).find("option:selected").text() : "None";
    $(label).text( newText );
};


/* "links" a source field to a set of target fields;
 * sets the target fields' values according to the targets dictionary
 * when the source field equals 'linkingValue"
 * (targets must be in the same form/subform)
 */
function link(source,linkingValue,targets) {
   var sourceValueMatches = false;
   var sourceType = $(source).attr("type");
   if (sourceType == "checkbox") {
     //if (((linkingValue.toLowerCase()=="true") && ($(source).is(":checked")))) || ((linkingValue.toLowerCase()=="false") && (1))) {
     if ( ( ( linkingValue.toLowerCase()=="true" ) && ( $(source).is(":checked") ) )  || ( ( linkingValue.toLowerCase()=="false" ) && !( $(source).is(":checked") ) ) ) {
         sourceValueMatches = true;
     }
   }
   // TODO: ADD MORE CASES FOR OTHER TYPES OF SOURCE FIELDS
   else {
       alert("I don't know what to in the function 'link()' with a source of type '" + sourceType + "'.");
   }

   if (sourceValueMatches) {
       for(var targetName in targets) {
           var targetValue = targets[targetName];
           var selector = ".field[name='" + targetName + "']";
           // the target can either be an <input> or a <select>
           // TODO: CAN IT BE ANYTHING ELSE?
           var target = $(source).closest(".form").find(selector).find("input,select");
           var targetType = $(target).attr("type");
           if (targetType=="checkbox") {
               if (targetValue.toLowerCase()=="true") $(target)..attr('checked', true);
               if (targetValue.toLowerCase()=="false") $(target).attr('checked', false);
           }
           // TODO: ADD MORE CASES FOR OTHER TYPES OF TARGET FIELDS
           else {
               alert("I don't know what to in the function 'link()' with a target of type '" + targetType + "'.");
           }
       }
   }
};

   var customTreeMenu = {

                   
                };
                
/* replace the default treeview menu w/ my custom code */
function customNavTreeMenu(node) {
    var items = {
        "insertItem" : {
            "label" : "Insert Child Component",
            // TODO: FN TO INSERT
            "action" : function (obj) {alert(1); /* this is the tree, obj is the node */},
        },
        "deleteItem" : {
            "label" : "Delete Component",
            // TODO: FN TO DELETE
            "action" : function (obj) {alert(1); /* this is the tree, obj is the node */},
        }
    };

    if ($(node).parents("li").length == 0) {
        // if there are no parents,
        // don't enable deletion
        items.deleteItem._disabled = true
    }

    return items;
}

/* enable jquery widgets */
function enableJQueryWidgets() {
    $(function() {

        /* enable the dialog boxes */
        $("#help-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#confirm-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
            /*
            ,buttons: {
                ok : function() {
                    $( this ).dialog( "close" );
                },
                cancel : function() {
                    $( this ).dialog( "close" );
                }
            }
            */
        });
        $("#edit-dialog").dialog({
           autoOpen:false,hide:'explode',modal:true         
        });
        $("#add-field-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#remove-field-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#saved-form-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });
        $("#published-form-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true
        });

        /* add functionality to help-buttons (icons masquerading as buttons) */        
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
           /* since metadata works with sub-applications, there may be periods in the ids */
           /* I escape them so that javascript doesn't interepret them as class selectors */
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


    


        /* enable the splitter */
        $("#splitter").splitter({
            type : "v",
            dock: "left",
            dockSpeed: 400,
            outline: true,
            sizeLeft: true
        });
        $(".splitter-bar").attr(
            /* add a tooltip to the splitter */
            "title","Click to toggle navigation menu."
        );
        $(".splitter-bar").append(
            /* add a JQuery image to the splitter */
            "<span class='ui-icon ui-icon-arrowthickstop-1-w'></span>"
        );
        $(".splitter-bar").find("span.ui-icon").css(
            /* position that image in the middle of the splitter */
            "margin-top", (($("#splitter").height()-16)/2)
        );
        $("#splitter").find(".splitter-bar").click(function() {
            /* dock/undock the splitter upon clicking */
            $(this).trigger("toggleDock");
            /* and change the image accordingly */
            var icon = $(this).find("span.ui-icon");
            $(icon).toggleClass("ui-icon-arrowthickstop-1-w");
            $(icon).toggleClass("ui-icon-arrowthickstop-1-e");            
        });

        /* enable treeview */
        $("#navTree").bind("loaded.jstree", function(event,data){
            data.inst.open_all(-1);
        });
        $("#navTree").bind("refresh.jstree", function (event, data) {
            data.inst.open_all(-1);
        });
        $("#navTree").jstree({
            "plugins" : ["themes","types","json_data","ui","crrm","contextmenu"],
            "themes" : {icons : true, url : "/static/dcf/css/jstree/style.css"},
            "types" : {
              /* TODO: TYPES (CUSTOM ICONS) NOT WORKING ?!? */
              /* (needs to use "rel" attribute?) */
              "complete" :      {"icon" : {"image" : "/static/dcf/img/jstree_complete.png"}},
              "incomplete" :    {"icon" : {"image" : "/static/dcf/img/jstree_incomplete.png"}},
              "valid" :         {"icon" : {"image" : "/static/dcf/img/jstree_valid.png"}},
              "invalid" :       {"icon" : {"image" : "/static/dcf/img/jstree_invalid.png"}}
          
            },
            "json_data" : {
                "ajax" : {
                    "url" : "ajax/component_nest",
                    "data" : function (n) {
                        return {guid : GLOBAL_DOCUMENT_GUID};
                    }
		}
            },
            "contextmenu" : {items : customNavTreeMenu}
        });
            
        $("#navTree").bind("select_node.jstree", function (event, data) {
            var node = data.rslt.obj;
            var guid = $(node).attr("id")
            // TODO: FN TO SHOW/HIDE RIGHTPANE
            // HERE IS HOW YOU RELOAD THE TREE:
            // $("#navTree").jstree("refresh");
            alert("you clicked item:  " + guid)
            $("#navTree").jstree("set_type","commplete",node);
        });

        /* enable multi-open accordions */
        $(".accordion").multiOpenAccordion({
            active : "all",
            tabShown : function(event,ui) {
               var activeTab = ui["tab"];
               var activeContent = ui["content"];
               if ($(activeTab).hasClass("sorted")) {
                   /* if the accordion content is being open just b/c it was clicked during sorting */
                   /* then hide it and reset all relevant styles */
                   $(activeContent).hide();
                   $(activeTab).removeClass("sorted ui-state-active");
                   $(activeTab).addClass("ui-state-default");
                   var activeTabIcon = $(activeTab).find("span");
                   $(activeTabIcon).removeClass("ui-icon-triangle-1-s");
                   $(activeTabIcon).addClass("ui-icon-triangle-1-e");
               }
               else {
                   /* otherwise set a class to override the default open style */
                   $(activeTab).addClass("open-accordion");
               }
           },
           tabHidden : function(event,ui) {
               var activeTab = ui["tab"];
               $(activeTab).removeClass("open-accordion");
           }
        });
        /* enable sortable multi-open accordions */
        $(".accordion").find(".accordion-header").each(function() {
            /* first wrap each accordion header & content pair in a div */
            /* b/c the sortable items need to be a single unit */
            var div = "<div class='sortable-item'></div>";
            $(this).next().andSelf().wrapAll(div);
        });
        $(".accordion").sortable({
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
                    $(this).find("div.field[name='order']>input").val(i+1);
                });
            }
            /* TODO: JQUERY DOCUMENTATION IMPLIES SOME MORE CODE HERE TO HANDLE IE BUG */
        });

        /* enable _fancy_ buttons */
        $(".button").button();        
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

        /* USING CONTEXT MENU INSTEAD OF BUTTONS TO INSERT/DELETE COMPONENTS */
        /*
        $(".navtree-toolbar button.insert" ).button({
             icons : {primary: "ui-icon-circle-plus"},
             text : false
        });
        $(".navtree-toolbar button.delete" ).button({
             icons : {primary: "ui-icon-circle-minus"},
             text : false
        });
        $(".navtree-toolbar button.expand" ).button({
             icons : {primary: "ui-icon-circle-triangle-s"},
             text : false
        });
        $(".navtree-toolbar button.collapse" ).button({
             icons : {primary: "ui-icon-circle-triangle-n"},
             text : false
        });
        */

       /* enable collapsible fieldsets */
       $(".coolfieldset").coolfieldset({speed:"fast"});

       /* enable tagging functionality for field types (in customization form) */
       $("#field-types").tagit({
           allowSpaces : true,
           singleField : true,
           singleFieldDelimiter : "|",
           onTagExists : function(event,ui) {
               /*
               var x = $(this).offset().left - $(document).scrollLeft();
               var y = $(this).offset().top - $(document).scrollTop();
               var title = "error";
               $("#help-dialog").html("Field type names must be unique.");
               $("#help-dialog").dialog("option",{title: title, position: [x,y], height: 200, width: 400}).dialog("open");
               */
           },
           afterTagAdded : function(event, ui) {
               var newTag = ui.tag
               var newTagName = $(newTag).find(".tagit-label").text();
               var newTagKey = newTagName.replace(/ /g,'')
               var newTagPk = "" // set by AJAX below

               var modelName = $("div.vars span[name='modelName']").text()
               var appName = $("div.vars span[name='appName']").text()

               var url = window.document.location.protocol + "//" + window.document.location.host + "/metadata/ajax/get_field_category";
               url += "?k=" + newTagKey + "&n=" + newTagName + "&m=" + modelName + "&a=" + appName;

               // when() is a new JQuery fn;
               // in theory it waits until the call to ajax() returns
               // (haven't tested this robustly)
               $.when(
                   $.ajax({
                       url : url,
                       dataType : "json",
                       success : function(data) {
                           // store the JSON serialization (plus the pk) of the object in the "categories" dictionary
                           categories[newTagKey] = data["fields"];
                           categories[newTagKey]["pk"] = data["pk"];
                       }
                   })
                ).done(function() {                    
                    initializeTag(newTag);
                    $(newTag).find(".tagit-show").button({
                        text : false,
                        icons : {
                            primary : "ui-icon-lightbulb"
                        }
                    }).click(function() {
                        // toggle all fields w/ this category
                        newTagPK = categories[newTagKey]["pk"];
                        $("div.field[name='category']").find("select").each(function() {                            
                            if ($(this).find("option:selected").val()==newTagPK) {
                                var section = $(this).closest(".sortable-item");                                
                                $(section).toggle();
                            }
                        });
                        
                        $(this).button("refresh");
                    });

                    /* this may be overkill (reordering _all_ tags instead of just the new one) */
                    reorderTags();
                    
                    $("div.field[name='category']").find("select").each(function(){
                        var newTagValue = categories[newTagKey].pk;
                        var selector = "option[value='" + newTagValue + "']";
                        if ($(this).find(selector).length==0) {
                            var newOption = new Option(newTagName,newTagValue)
                            $(this).append(newOption);
                        }
                   });
               
                });
           },
           beforeTagRemoved : function(event, ui) {
               var text = "Deleting this Field Type is permanent.  Any fields of this type will no longer have a type.  Are you sure you wish to continue?"
               return confirm(text);
/*
*              NOT USING JQUERY HERE B/C IT IS MULTI-THREADED
*              & WON'T WAIT FOR DIALOG RESPONSE BEFORE REMOVING TAG
*              TODO: THE CONFIRM BOX LOOKS UGLY; IS THERE A WAY TO USE DIALOG AFTER ALL?
               var title = "Delete Field Type";
               var text = "Deleting this Field Type is permanent.  Any fields of this type will no longer have a type.  Are you sure you wish to continue?"
               $("#help-dialog").html(text);
               $("#help-dialog").dialog("option",{
                   title: title,
                //   position: [x,y],
                   height: 200,
                   width: 400,
                   buttons : {
                       ok : function() { 
                           $( this ).dialog( "close" );
                           return true;
                       },
                       cancel : function() {
                           $( this ).dialog( "close" );
                           //$("#field-types").tagit("createTag",ui.tagLabel)
                           return false;
                       }
                   }
               }).dialog("open");
*/
           },
           afterTagRemoved : function(event, ui) {
               var oldTag = ui.tag
               var oldTagName = $(oldTag).find(".tagit-label").text();
               var oldTagKey = oldTagName.replace(/ /g,'')
               var oldTagValue = categories[oldTagKey].pk;

               var modelName = $("div.vars span[name='modelName']").text()
               var appName = $("div.vars span[name='appName']").text()

               var url = window.document.location.protocol + "//" + window.document.location.host + "/metadata/ajax/delete_field_category";
               url += "?k=" + oldTagKey + "&m=" + modelName + "&a=" + appName;

               $.ajax({
                   url : url,
                   dataType : "json",
                   success : function(data) {
                       // the AJAX fn deletes the category from the db
                       // now delete it from the javascript variable
                       // and re-order all the remaining categories in that variable accordingly                       
                       oldCategoryOrder = categories[oldTagKey].order;
                       delete(categories[oldTagKey]);
                       reorderTags();
                   }
               })

               $("div.field[name='category']").find("select").each(function(){
                   // after the tag is removed, go through all field-type selects...
                   var selector = "option[value='" + oldTagValue + "']";
                   var oldOption = $(this).find(selector);
                   // and remove the corresponding option...
                   $(oldOption).remove();
                   if ($(oldOption).attr("selected")=="selected") {
                       // and force a change event if that option had been selected
                       $(this).trigger("change");
                   }

                   // need to show this (accordion) section in case it had been hidden before...
                   var section = $(this).closest(".sortable-item");
                   if (!$(section).is(":visible")) {
                       $(section).toggle();
                   }
                   
               });
           }

       });
       $(".tagit-new").attr("title","Enter new field categories here");
       $(".tagit").sortable({
            axis : "x",         
            items : "li:not(.tagit-new)",
            placeholder : "sortable-tag-placeholder",
            stop : function( event, ui ) {
                /* after sorting the tags, reorder the field-types input to match */
                var sortedItem = ui["item"];
                var sortedItems = $(sortedItem).closest("ul.tagit").find("li.tagit-choice");                
                var orderedFieldList = $(sortedItems).map(function() {
                    return $(this).find(".tagit-label").text();
                }).get().join("|");
                $("#field-types").val(orderedFieldList);
                /* and reorder the global javascript dictionary of categories */
                reorderTags();
            }

       });
       
    });


};
