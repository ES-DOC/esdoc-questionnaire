/* global vars */
var CATEGORIES = {}
var ATTRIBUTE_CATEGORIES = {}
var PROPERTY_CATEGORIES = {}

/* main fn */
var CUSTOMIZE = {
    enableDCF : function() {

        /* enable the sort button */
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
            //$(this).menu().width($(sort_button).width()).hide();
            $(this).menu().width("8em").hide();
        });
        $(".sort_by").click(function(event){
            var sort_key = $(event.target).attr("name");
            var items_to_sort = $(event.target).closest(".tab_content").find(".accordion:first");
            sort_accordions(items_to_sort,sort_key);        // call the sort fn with the specified key & target
            $(event.target).closest(".sort_by").hide();     // hide the sort_by menu
            event.preventDefault();     // don't actually follow the menu link (one of these is bound to work)
            return false;               // don't actually follow the menu link (one of these is bound to work)
        });

        /* enable the tagging widgets */
        $(".tags").tagit({
           allowSpaces : true,
           singleField : true,
           singleFieldDelimiter : "|",

           afterTagAdded : function(event,ui) {
               var newTag       = ui.tag
               var newTagName   = $(newTag).find(".tagit-label").text();
               var newTagKey    = newTagName.toLowerCase().replace(/ /g,'')
               var newTagType   = $(newTag).closest(".tagit").prev("input.tags").attr("name");

               if (newTagType.indexOf("attribute")>=0) {
                   newTagType = "attribute";
                   categories = ATTRIBUTE_CATEGORIES;
               }
               else if (newTagType.indexOf("property")>=0) {
                   newTagType = "property";
                   categories = PROPERTY_CATEGORIES;
               }

               var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/get_category/" + newTagType;
               url += "?k=" + newTagKey + "&n=" + newTagName + "&v=" + VERSION + "&p=" + PROJECT + "&m=" + MODEL

               // TODO: when() is a new JQuery fn;
               // in theory it waits until the call to ajax() returns
               // (haven't tested this robustly)
               $.when(
                   $.ajax({
                       url : url,
                       dataType : "json",
                       success : function(data) {
                           // store the JSON serialization of the object in the global dictionary

               // TODO: NEED TO FIGURE OUT A BETTER WAY TO COMPUTE THIS
               // I'M DOING IT TWICE B/C AJAX IS ASYNCHRONOUS
               // SO categories COULD BE SET TO SOMETHING ELSE BY THE TIME I GET HERE
               if (newTagType.indexOf("attribute")>=0) {
                   newTagType = "attribute";
                   categories = ATTRIBUTE_CATEGORIES;
               }
               else if (newTagType.indexOf("property")>=0) {
                   newTagType = "property";
                   categories = PROPERTY_CATEGORIES;
               }

                           categories[newTagKey] = data["fields"];
                           categories[newTagKey]["type"] = newTagType
                           categories[newTagKey]["pk"] = data["pk"]
                           
                       }
                   }).done(function() {
                        // setup the look-and-feel and behavior of the new tag
                        initialize_tag(newTag,categories[newTagKey])
                        // add that tag to the set of available categories to assign attributes/properties to
                        
                        
                        $(newTag).closest(".tab_content").find(".field_value[name='category'] select").each(function() {
                            var newTagValue = categories[newTagKey].pk
                            var selector = "option[value='"+newTagValue+"']";
                            if ($(this).find(selector).length==0) {
                                var new_option = new Option(newTagName,newTagValue);
                                $(this).append(new_option);
                            }
                    });

                    
                        var ordered_tag_list = $(newTag).closest("ul.tagit").find("li.tagit-choice").map(function() {
                           return $(this).find(".tagit-label").text();
                       }).get().join("|");
                       // TODO: ONLY WANT TO CALL THIS WHEN _ALL_ TAGS HAVE BEEN ADDED?
                       // MAYBE ADD THINGS TO A QUEUE?
                       order_categories(newTagType,ordered_tag_list)

                   })
               );

           },

           beforeTagRemoved : function(event,ui) {
               // TODO: use JQuery dialog method instead of JS confirm method.
               var text = "Deleting this category is permanent.  Any properties belonging to this category will become uncategorized.  Are you sure you wish to continue?"
               return confirm(text);
           },

           afterTagRemoved : function(event, ui) {
               var oldTag       = ui.tag
               var oldTagName   = $(oldTag).find(".tagit-label").text();
               var oldTagKey    = oldTagName.toLowerCase().replace(/ /g,'')
               var oldTagType   = $(oldTag).closest(".tagit").prev("input.tags").attr("name");
               var oldTagWidget = $(oldTag).closest("ul.tagit");

               if (oldTagType.indexOf("attribute")>=0) {
                   oldTagType = "attribute";
                   categories = ATTRIBUTE_CATEGORIES;
               }
               else if (oldTagType.indexOf("property")>=0) {
                   oldTagType = "property";
                   categories = PROPERTY_CATEGORIES;
               }

               var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/delete_category/" + oldTagType;
               url += "?k=" + oldTagKey + "&n=" + oldTagName + "&v=" + VERSION + "&p=" + PROJECT + "&m=" + MODEL

                $.ajax({
                   url : url,                
                   success : function(data) {
                       // the AJAX fn deletes the category from the db
                       // now delete it from the javascript variable...
                       var oldTagValue = categories[oldTagKey].pk
                       delete(categories[oldTagKey]);
                       // and re-order all the remaining categories in that variable accordingly...
                       var ordered_tag_list = $(oldTagWidget).find("li.tagit-choice").map(function() {
                           return $(this).find(".tagit-label").text();
                       }).get().join("|");
                       order_categories(oldTagType,ordered_tag_list);
                       // and remove that tag's content from any selects...                       
                       $(oldTagWidget).closest(".tab_content").find(".field_value[name='category'] select").each(function() {
                            var selector = "option[value='"+oldTagValue+"']";
                            var old_option = $(this).find(selector);
                            $(old_option).remove();
                            if ($(old_option).attr("selected")=="selected") {
                                $(this).trigger("change");
                            }
                            var section = $(this).closest(".sortable-item");
                            if (!$(section).is(":visible")) {
                                $(section).toggle()
                            }
                        });
                   }
               });
           }
        });
        $(".tagit-label").each(function() {
            $(this).attr("title","click to toggle attributes of this category");
        });
        /* I'm using separate widget to add tags, so disable the .tagit-new box */
        $(".tagit-new").attr("style","display:none!important;");
        /* and enable this widget */
        $("#property_categories_tags_add").keypress(function(e) {
            if(e.which == 13) {
                var input = $(e.target)
                var tag_name = $(input).val();
                var tag_widget = $(input).closest(".tab_content").find(".tags");
                if ($(tag_widget).tagit("createTag",tag_name)) {
                    $(input).val("");
                }
                return false;
            }
        });
        /* finally, make the tags sortable */
        $(".tagit").sortable({
            axis : "x",
            items : "li:not(.tagit-new)",
            placeholder : "sortable-item",
            stop : function( event, ui ) {
                var sorted_item = ui["item"];
                var sorted_items = $(sorted_item).closest("ul.tagit").find("li.tagit-choice");
                var category_type = $(sorted_item).closest("ul.tagit").prev("input.tags").attr("name");
                var ordered_tag_list = $(sorted_items).map(function() {
                    return $(this).find(".tagit-label").text();
                }).get().join("|");
                order_categories(category_type,ordered_tag_list);
            }
        });

        
    }
    /* end enableDCF fn */
};

function sort_accordions(accordions,key) {

    if (key.indexOf("name")>=0) {
        key_selector = "span[name='field-name']";
    }
    else if (key.indexOf("category")>=0) {
       key_selector = "span[name='field-category']";
    }
    else if (key.indexOf("order")>=0) {
       key_selector = "span[name='field-order']";

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


function initialize_tag(tag,category) {
    /* initialize the look-and-feel and behavior of this tag
     * (depends on whether it represents an attributecategory or propertycategory)
     * tag is the tag-it widget, category is the entry from the global dictionary */

    var isEditable = category["type"]=="attribute";

    // * add a handler for showing/hiding fields of this category */
    $(tag).click(function(event){
        // if you really clicked the tag, and not an icon/button on the tag...
        if ($(event.target).attr("class").indexOf("ui-icon") == -1) {
            // toggle its state..
            $(this).toggleClass("ui-state-active");
            // and that of all corresonding attributes/properties...
            $(this).closest(".tab_content").find(".accordion-header .label[name='field-category']").each(function() {
                if ($(this).text()==category["name"]) {
                    var section = $(this).closest(".sortable-item");    // this is the accordion (recall it's wrapped in a div to enable sorting)
                    $(section).toggle();
                }
            });
        }
    });

    /* if the tag is for a property, then add the edit icon */
    if (!isEditable) {
        $(tag).find(".tagit-label").before(
            "<a class='tagit-edit' onclick='edit_tag(this);'><span class='ui-icon ui-icon-pencil'></span></a>"
        );
    }

    /* if the tag is for an attribute, then disable the close icon */
    if (isEditable) {
        $(tag).find(".tagit-close").hide();
    }

};

function edit_tag(edit_tag_icon) {
    var tagName = $(edit_tag_icon).next(".tagit-label").text();
    var tagKey = tagName.toLowerCase().replace(/ /g,'');
    var category_type = $(edit_tag_icon).closest("ul.tagit").prev("input.tags").attr("name");


    if (category_type.indexOf("attribute")>=0) {
        category_type = "attribute";
        categories = ATTRIBUTE_CATEGORIES;
    }
    else if (category_type.indexOf("property")>=0) {
       category_type = "property";
       categories = PROPERTY_CATEGORIES;
    }

    var category = categories[tagKey];

    var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/edit_category/" + category_type;
    url += "?k=" + tagKey + "&n=" + tagName + "&v=" + VERSION + "&p=" + PROJECT + "&m=" + MODEL

    // copy over the values from category (they'll be more up-to-date than the db'
    for (var key in category) {
        if (category.hasOwnProperty(key)) {
            url += "&" + key + "=" + category[key];
        }
    }
    
    $.ajax({
         url : url,
         success : function(data) {
             var title = "Edit Category";
             $("#edit-dialog").html(data);
             $("#edit-dialog").dialog("option",{
                 title : title,
                 height: 300,
                 width: 700,
                 buttons : {
                     ok : function() {
                         
                         var data = serialize_form($(this).find("form"),"JSON");
                         for (var key in data) {
                             category[key] = data[key]
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

function order_categories(category_type,ordered_tag_list) {
  if (category_type.indexOf("attribute")>=0) {
    category_type = "attribute";
    categories = ATTRIBUTE_CATEGORIES;
  }
  else if (category_type.indexOf("property")>=0) {
    category_type = "property";
    categories = PROPERTY_CATEGORIES;
  }
  ordered_tag_list = ordered_tag_list.split("|");
  for (var i=0; i<ordered_tag_list.length; i++) {
      tag_name = ordered_tag_list[i];
      tag_key = tag_name.toLowerCase().replace(/ /g,'');
      if (categories.hasOwnProperty(tag_key)) {
          categories[tag_key].order = i+1;
      }
  }


};
