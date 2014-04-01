/* functions specific to the customizer */

var SAMPLE_CATEGORY = {
    "pk"        : "null",
    "model"     : "questionnaire.metadatascientificcategory.customizer", // only scientific categories can be added to
    "fields"    : {
        "name"          : "sample", // to be overwritten
        "key"           : "sample", // to be overwritten
        "description"   : null,     // to be overwritten
        "vocabulary"    : null,     // to be set in the view
        "last_modified" : null,     // to be set in the view
        "proxy"         : null,     // an added category will have no proxy
        "order"         : 0,        // to be overwritten
        "pending_deletion"  : false
    }
}

function vocabularies(parent) {
    $(parent).find("select[name='vocabularies'].multiselect").multiselect({
        autoOpen    : true,
        header      : false,
        height      : 'auto',
        beforeclose : function(event,ui) {
            return false;
        }
    });
}

function tags(parent) {
    $(parent).find(".tags").each(function() {
        var tag_widget  = $(this);
        var tag_type    = $(tag_widget).attr("name");
        
        $(this).tagit({
            allowSpaces : true,
            singleField : true,
            singleFieldDelimiter : "|",
            caseSensitive : false,
            afterTagAdded : function(event,ui) {
                var tag = ui.tag;
                var tag_name = $(tag).find(".tagit-label").text();
                var tag_key = slugify(tag_name);
                var tag_order = $(tag).closest(".tagit").find(".tagit-choice").length;

                var widget_id           = $(this).attr("id");
                var widget_name         = $(this).attr("name")
                var tag_content_widget  = $("textarea[id='"+widget_id.replace(/_tags$/,"_content")+"']");
                var tag_content         = $.parseJSON($(tag_content_widget).val());

                
                if (tag_type == "standard_categories_tags") {
                    $(tag).find(".tagit-close").hide();
                }
                $(tag).find(".tagit-label").before(
                    "<a class='tagit-edit' onclick='edit_tag(this);'><span class='ui-icon ui-icon-pencil'></span></a>"
                );
                $(tag).find(".tagit-label").attr("title","click to toggle properties belonging to this category");

                var tag_just_added = $(tag).hasClass("added");
                if (tag_just_added) {
    
                    var new_category = $.extend(true,{},SAMPLE_CATEGORY);   // this does a deep copy of the object
                    
                    new_category.pk             = "null";
                    new_category.fields.name    = tag_name;
                    new_category.fields.key     = tag_key;
                    new_category.fields.order   = tag_order;
                    new_category.fields.pending_deletion = false;

                    tag_content.push(new_category);
                    $(tag_content_widget).val(JSON.stringify(tag_content));
                    
                    // TODO: ADD OPTION
                    $(tag_content_widget).closest(".form").find("select[name$='-category']").each(function() {
                        // add option
                        $(this).append('<option value="' + tag_key + '">' + tag_name + '</option>');
                        $(this).next(".ui-multiselect").append(
                            "<label previous_value='unchecked' style='display: block;' for='"+widget_id+"-"+tag_key+"'>\
                                <input id='"+widget_id+"-"+tag_key+"' name='"+widget_name+"' type='radio' value='"+tag_key+"'>&nbsp;"+tag_name+"</input>\
                            </label>");
                    });

                    $(tag).removeClass("added");
                    
                }
            },
            beforeTagRemoved : function(event,ui) {
                var tag = ui.tag;
                var tag_name = $(tag).find(".tagit-label").text();
                var tag_key  = slugify(tag_name);
                var tag_id              = $(this).attr("id");
                var tag_content_widget  = $("textarea[id='"+tag_id.replace(/_tags$/,"_content")+"']");
                var tag_content         = $.parseJSON($(tag_content_widget).val());

                if (tag_type == "standard_categories_tags") {
                    alert("You shouldn't be deleting standard categories.  You're a very naughty boy.");
                }
                $("#confirm_dialog").html("Any properties belonging to this category will become uncategorized.  Are you sure you wish to continue?");
                $("#confirm_dialog").dialog("option",{
                   title        : "Delete Category?",
                   dialogClass  : "no_close",
                   height       : 200,
                   width        : 400,
                   buttons: {
                       ok : function() {
                            $.each(tag_content,function(i,object){
                                if (object.fields.name == tag_name) {
                                    object.fields.pending_deletion = true;
                                }
                            });
                            $(tag_content_widget).val(JSON.stringify(tag_content));
                            $(tag_content_widget).closest(".form").find("select[name$='-category']").each(function() {                                
                                $(this).find("option:contains("+tag_name+")").remove();
                                $(this).next(".ui-multiselect").find("label:contains('"+tag_name+"')").remove();
                                $(this).trigger("change");
                            });
                            $(this).dialog("close");
                       },
                       cancel : function() {
                           // the tag data is still in categories; just put it back in the widget
                           var tag_widget = $(event.target);
                           $(tag_widget).tagit("createTag",tag_name);
                           $(this).dialog("close");
                       }
                   }
               }).dialog("open");
            }
        });
        $(parent).find(".tagit").sortable({
            axis        : "x",
            items       : "li:not(.tagit-new)",
            placeholder : "sortable_item",
            start : function(e, ui){
                ui.placeholder.height(ui.item.height());
                ui.placeholder.width(ui.item.width());
            },
            stop  : function(e, ui) {
                var tag_id              = $(this).prev(".tags").attr("id")
                var tag_content_widget  = $("textarea[id='"+tag_id.replace(/_tags$/,"_content")+"']");
                var tag_content         = $.parseJSON($(tag_content_widget).val())

                new_tag_order = $(this).find(".tagit-choice").map(function() {
                    return $(this).find(".tagit-label").text()
                }).get();
                for (var order=0; order<new_tag_order.length; order++) {
                    tag_name = new_tag_order[order];
                    $.each(tag_content,function(i,object) {
                       if (object.fields.name == tag_name) {
                           object.fields.order = (order + 1);   // js is 0-based, django is 1-based
                           return false;                        // break out of the loop
                       }
                    });
                }
                $(tag_content_widget).val(JSON.stringify(tag_content));
            }
        });
        // rather than set 'readonly' to true (since I still want the functionality),
        // I just hide that part of the widget...
        $(parent).find(".tagit-new").hide();
        // ...and add code to this dummy widget...
        var add_tag = $(this).nextAll(".add_tag:first");
        if (tag_type == "standard_categories_tags") {
            $(add_tag).hide()
        }
        // ...(but only for scientific categories)...
        else {
            $(add_tag).find("input").keypress(function(e){
                var ENTER = 13
                if(e.which == ENTER) {
                    var tag_name = $(this).val();
                    var tag_widget = $(add_tag).prevAll(".tags:first");
                    var add_success = $(tag_widget).tagit("createTag",tag_name,"added")                    
                    if (add_success) {
                        $(add_tag).find("input").val("");
                    }
                    alert("one")
                    e.preventDefault();
                    alert("two")
                    return false;
                    alert("three")
                }
            });
        }
    });
}

function sortable_accordions(parent) {
    $(parent).find(".accordion").find(".accordion_header").each(function() {
        /* wrap each accordion header & content pair in a div */
        /* b/c they need to be a single unit to be sortable */
        var accordion_unit = "<div class='accordion_unit'></div>";
        $(this).next().andSelf().wrapAll(accordion_unit);
    });
    $(parent).find(".accordion").sortable({
        axis        : "y",
        items       : "accordion_unit",//"h3",
        placeholder : "sortable_item",
        start : function(e,ui){
            ui.placeholder.height(ui.item.height());
            ui.placeholder.width(ui.item.width());
        },
        stop : function(e,ui) {
            var accordion_header = ui["item"];
            $(accordion_header).addClass("sorting");
            
            $(accordion_header).closest(".accordion").find(".accordion_header").each(function(i) {
                var accordion_order = $(this).find("input.label[id$='-order']");
                $(accordion_order).val(i)
            });

        }
    });
}
  
function edit_tag(edit_tag_icon) {
    var tag_name        = $(edit_tag_icon).next(".tagit-label").text();
    var tag_key         = slugify(tag_name);
    var tag_widget      = $(edit_tag_icon).closest(".tagit").prev(".tags");
    var tag_id          = $(tag_widget).attr("id")
    var tag_content_widget      = $("textarea[id='"+tag_id.replace(/_tags$/,"_content")+"']");
    var tag_content             = $.parseJSON($(tag_content_widget).val());

    var category_to_edit = "";
    $.each(tag_content,function(i,category) {
       var category_fields = category.fields
       console.log(category_fields.key + " == " + tag_key + " ?");

       if ((category_fields.key == tag_key)) {
           category_to_edit = category;
           return false;    // break the each loop
       }
    });

    
    
    url = window.document.location.protocol + "//" + window.document.location.host + "/ajax/customize_category/";
    url += "?n=" + category_to_edit.fields.name +
           "&k=" + category_to_edit.fields.key +
           "&d=" + category_to_edit.fields.description +
           "&o=" + category_to_edit.fields.order +
           "&m=" + category_to_edit.model

    var edit_dialog = $("#edit_dialog");
    $.ajax({
        url     : url,
        type    : "GET",
        cache   : false,
        success : function(data) {
            $(edit_dialog).html(data);
            $(edit_dialog).dialog("option",{
                height      : 400,
                width       : 800,
                dialogClass : "no_close",
                title       : "Edit Category",                
                open : function() {
                    // apply all of the JQuery code to _this_ dialog
                    var parent = $(edit_dialog);
                    init_widget(readonlies,parent);
                    init_widget(buttons,parent);
                    init_widget(helps,parent);
                },                
                buttons     : {
                    ok : function() {
                        form_data = $(this).find("form#category").serializeArray();
                        for (var i=0; i<form_data.length; i++) {
                            field_data = form_data[i];
                            category_to_edit.fields[field_data.name] = field_data.value;
                        }
                        $(tag_content_widget).val(JSON.stringify(tag_content));
                        $(edit_dialog).dialog("close");
                    },
                    cancel : function() {
                        $(edit_dialog).dialog("close");
                    }
                }
                /*
                 * (not needed since we're using an existing div)
                close : function() {
                    $(this).dialog("destroy");
                }
                */
            }).dialog("open");
            
        }
    });
}

/* based on the enable() fn, which enables seaprate fields,
 *  this is a special case just for enabling the customize subform button */
function enable_customize_subform_button(source) {

    var source_value_matches = $(source).is(":checked");
    var target_button = $(source).closest(".field").find("button[name='customize_subform']")

    if (source_value_matches) {
        $(target_button).removeClass("ui-state-disabled");
        $(target_button).prop("disabled",false)
    }
    else {
        $(target_button).addClass("ui-state-disabled");
        $(target_button).prop("disabled",true)
    }
};

function customize_property_subform(subform_id) {

    url = window.document.location.protocol + "//" + window.document.location.host + "/ajax/customize_subform/";
    url += "?i=" + subform_id;
    
    var customize_subform_dialog = $("#customize_subform_dialog");
    
    $.ajax({
        url     : url,
        type    : "GET",
        cache   : false,
        success : function(data) {
            $(customize_subform_dialog).html(data);
            $(customize_subform_dialog).dialog("option",{
                height      : 800,
                width       : 1200,
                dialogClass : "no_close",
                title       : "Customize Subform",
                open : function() {
                    // apply all of the JQuery code to _this_ dialog
                    var parent = $(customize_subform_dialog);
                    init_widget(readonlies,parent);
                    init_widget(buttons,parent);
                    init_widget(fieldsets,parent);
                    init_widget(selects,parent);
                    init_widget(accordions,parent);
                    init_widget(helps,parent);
                    init_widget(enablers,parent);

                },
                buttons     : {
                    ok : function() {
                        $(customize_subform_dialog).dialog("close");
                    },
                    cancel : function() {
                        $(customize_subform_dialog).dialog("close");
                    }
                }
            }).dialog("open");
        }
    });
  
};