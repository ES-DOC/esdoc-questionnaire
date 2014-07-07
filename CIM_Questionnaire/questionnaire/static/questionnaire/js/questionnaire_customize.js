/* functions specific to the customizer */

var STANDARD_TAG_TYPE   = 0;
var SCIENTIFIC_TAG_TYPE = 1;

var SAMPLE_CATEGORY = {
    "pk"        : "null",
    "model"     : "questionnaire.metadatascientificcategorycustomizer", // only scientific categories can be added to
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
};

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
        var tag_type    = $(tag_widget).attr("name").endsWith("standard_categories_tags") ? STANDARD_TAG_TYPE : SCIENTIFIC_TAG_TYPE;

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

                
                if (tag_type == STANDARD_TAG_TYPE) {
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

                if (tag_type == STANDARD_TAG_TYPE) {
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
        if (tag_type == STANDARD_TAG_TYPE) {
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
                    e.preventDefault();
                    return false;
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
        items       : "div.accordion_unit",//"h3",
        placeholder : "sortable_item",
        start : function(e,ui){
            ui.placeholder.height(ui.item.height());
            ui.placeholder.width(ui.item.width());
        },
        stop : function(e,ui) {
            var accordion_unit = ui["item"];
            $(accordion_unit).find(".accordion_header").addClass("sorting");
            
            $(accordion_unit).closest(".accordion").find(".accordion_header").each(function(i) {
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

function customize_property_subform(subform_id,subform_customizer_field_name) {

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
                height      : 860,
                width       : 1200,
                dialogClass : "no_close",
                title       : "Customize Subform",
                open : function() {
                    // apply all of the JQuery code to _this_ dialog
                    var parent = $(customize_subform_dialog);
                    // the addition of the 'true' attribute forces initialization,
                    // even if this dialog is opened multiple times
                    init_widget(readonlies,parent,true);
                    init_widget(buttons,parent,true);
                    init_widget(fieldsets,parent,true);
                    init_widget(selects,parent,true);
                    init_widget(accordions,parent,true);
                    init_widget(helps,parent,true);
                    init_widget(enablers,parent,true);
                    init_widget(tags,parent,true);

                },
                buttons     : {
                    save : function() {
                        var subform_data = $(this).find("#customize_subform_form").serialize();                        

                        $.ajax({
                            url: url,
                            type: "POST",   // (POST mimics submit)
                            data: subform_data,
                            cache: false,
                            success : function(data,status,xhr) {
                                var status_code = xhr.status;
                                var msg = xhr.getResponseHeader("msg");
                                var instance_id = xhr.getResponseHeader("instance_id");
                                var msg_dialog = $(document.createElement("div"));
                                msg_dialog.html(msg);
                                msg_dialog.dialog({
                                    modal: true,
                                    hide: "explode",
                                    height: 200,
                                    width: 400,
                                    dialogClass: "no_close",
                                    buttons: {
                                        OK: function () {
                                            $(this).dialog("close");
                                        }
                                    }
                                });

                                if (status_code == 200) {
                                    $(customize_subform_dialog).dialog("close");
                                    var subform_customizer_field = $("select[name='"+subform_customizer_field_name+"']");
                                    $(subform_customizer_field).val(instance_id);
                                }
                                else {
                                    $(customize_subform_dialog).html(data);
                                    /* TODO: DO I HAVE TO RE-RUN INIT FNS? */
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
                    $(this).dialog("close");
                }
            }).dialog("open");
        }
    });  
};

function restrict_options(source,target_names) {

    restrictions = [];
    $(source).find("option:selected").each(function() {
        restrictions.push($(this).val());
    });

    // THIS IS HARD-CODED TO JUST WORK FOR MULTISELECT WIDGETS
    // B/C I ONLY USE THIS FOR ENUMERATION CHOICES & DEFAULTS
    for (var i=0; i<target_names.length; i++) {
        var selector = "select[name$='" + target_names[i] + "']:first";
        var target_element      = $(source).closest("div.form").find(selector);
        var target_element_id   = $(target_element).attr("id");
        var target_element_name = $(target_element).attr("name")

        var target_widget           = $(target_element).next(".ui-multiselect");
        var target_widget_contents  = $(target_widget).find(".multiselect_content");

        alert($(target_widget).attr("class"))
        
        var options = [];
        $(target_widget_contents).find("label").each(function() {
            options.push($(this).find("input").val())
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
            $(target_widget_contents).find("input[value='"+this+"']").parent("label").remove();
        });
        // add everything in restrictions and not in options
        $(in_restrictions_but_not_options).each(function() {
            var option = $(source).find("option[value='"+this+"']");
            var id = target_element_id + "-" + this;
            var new_multiselect_choice = $("<label previous_value='unchecked' style='display: block;' for='"+id+"'><input id='"+id+"' name='"+target_element_name+"' typee='checkbox' value='"+this+"'>&nbsp;"+$(option).text()+"</input></label>")

            $(target_widget_contents).append(new_multiselect_choice);
            
        });

    }
}
