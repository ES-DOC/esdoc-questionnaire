/* global vars */
var CATEGORIES = {}
var ATTRIBUTE_CATEGORIES = {}
var PROPERTY_CATEGORIES = {}

/* main fn */
var CUSTOMIZE = {
    enableDCF : function() {

        /* enable sortable multi-open accordions */
        $("#customize .accordion").find(".accordion-header").each(function() {
            /* first wrap each accordion header & content pair in a div */
            /* b/c the sortable items need to be a single unit */
            var div = "<div class='sortable-item'></div>";
            $(this).next().andSelf().wrapAll(div);
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
                    var order_input = $(this).find("input[name$='-order']")
                    $(order_input).val(i+1);
                    $(order_input).trigger("change");
                    //$(this).find("input[name$='-order']").val(i+1);

                });
            }
            /* TODO: JQUERY DOCUMENTATION IMPLIES SOME MORE CODE HERE TO HANDLE IE BUG */
        });

        /* enable the customize-subform button */
        $("button.customize-subform").button({
            icons : { primary : "ui-icon-extlink"}
        });
        /*.click(function(event) {
            var attribute_name = $(event.target).closest(".accordion-content").prev(".accordion-header");
            alert($(attribute_name).attr("class"));
            customize_subform();
        });
        */
        // force the change event to hide/show the customize-subform button as appropriate
        $(".field_value[name='customize_subform']").find("input").trigger("change");


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
/*
 * commented out: this just confuses things by remaining toggled 
        $(".tagit-choice").hover(function() {
            $(this).toggleClass("ui-state-hover");
        });
*/
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

function copy_tags_to_categories(tagsName,categoriesName) {
    
    var tags = window[tagsName];
    var categories = $("select[name='"+categoriesName+"']");
    var active_categories = Array();
    for (tag_key in tags) {
        var tag = tags[tag_key];
        active_categories.push(tag.pk);
    }
    $(categories).val(active_categories);

};

function copy_all_tags_to_all_categories() {
    copy_tags_to_categories("ATTRIBUTE_CATEGORIES","attribute_categories");
    copy_tags_to_categories("PROPERTY_CATEGORIES","property_categories");
};

function customize_subform(attribute_name,button) {
    
    var url = window.document.location.protocol + "//" + window.document.location.host + "/dcf/ajax/customize_subform/";
    url += "?a=" + attribute_name + "&m=" + MODEL + "&p=" + PROJECT + "&v=" + VERSION;

    var customize_subform_dialog = $("<div></div>");
    $.ajax({
         url        : url,
         type       : "GET",
         cache      : false,
         success    : function(data) {
            var title = "Customizing " + PROJECT + "::" + MODEL + "::" + attribute_name
            
            customize_subform_dialog.html(data);
            customize_subform_dialog.dialog({
                title : title,
                modal : true,
                dialogClass: "no-close",
                height : 400,
                width : 800,
                open : function() {
                    // apply all of the JQuery code to _this_ dialog
                    enableDCF();
                    render_msg(customize_subform_dialog);
                },
                buttons : {
                    ok : function() {
                       var attribute    = $(button).nextAll(".subform_customizer").find("select");
                       var subform_data = $(this).find("#customize_subform").serialize();
                       $.ajax({
                           url      : url,
                           type     : "POST",   // (POST mimics submit)
                           cache    : false,
                           data     : subform_data,
                           success  : function(data) {
                               // if the AJAX call returned JSON, then the form was valid
                               if (typeof data != 'string') { // == 'object') {
                                   // set the submodel attribute to the newly saved model
                                   var selector = "option[value='" + data.pk + "']";
                                   if ($(attribute).find(selector).length == 0) {
                                       $(attribute).append(new Option(data.unicode,data.pk));
                                   }
                                   $(attribute).val(data.pk);
                                   $(customize_subform_dialog).dialog("close");
                               }
                               // if the AJAX call returned a string, then the form was invalid
                               else {
                                   customize_subform_dialog.html(data);
                                   render_msg(customize_subform_dialog); // unlike the main forms, subforms have to explicitly call render_msg b/c they don't get re-opened on submit, the content just gets refreshed
                               }
                           },
                           error    : function(xhr,status,error) {                               
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
