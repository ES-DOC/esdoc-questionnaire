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

function tags(element) {

        var tag_widget  = $(element);
        var tag_type    = $(tag_widget).attr("name").endsWith("standard_categories_tags") ? STANDARD_TAG_TYPE : SCIENTIFIC_TAG_TYPE;

        $(tag_widget).tagit({
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
                    "<a class='tagit-edit' title='edit this category' onclick='edit_tag(this);'><span class='ui-icon ui-icon-pencil'></span></a>"
                );
                $(tag).find(".tagit-label").attr("title","click to toggle properties belonging to this category");
                $(tag).click(function(event) {
                    /* if you really clicked the tag, and not an icon/button on the tag... */
                    if ($(event.target).attr("class").indexOf("ui-icon") == -1) {
                        /* toggle its state... */
                        $(this).toggleClass("ui-state-disabled");
                        var tag_label = $(this).find(".tagit-label").text();
                        /* and that of all corresponding properties... */
                        $(this).closest(".tab_content").find(".accordion_header input.label[name$='category_name']").each(function() {
                            if ($(this).val()==tag_label) {
                                var section = $(this).closest(".accordion_unit");
                                $(section).toggle();
                            }
                        });
                    }
                });
                /*
                $(tag).find(".tagit-choice").click(function(event){
                    alert("clicked!");

                    if ($(event.target).attr("class").indexOf("ui-icon") == -1) {
                        $(this).toggleClass("ui-state-active");

                    }
                });
                */

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
        // now that the tagit widget has been created we can further customize it...
        var tagit_widget = $(tag_widget).next("ul.tagit:first");
        $(tagit_widget).sortable({
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
        $(tagit_widget).find(".tagit-new").hide();
        // ...and add code to this dummy widget...
        var add_tag = $(tagit_widget).nextAll(".add_tag:first");
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
}

function sortable_accordions(element) {
    /* element = $(parent).find(".accordion .accordion_header") */
    $(element).next().andSelf().wrapAll("<div class='accordion_unit'></div>");

    var accordion = $(element).closest(".accordion");
    $(accordion).sortable({
        axis        : "y",
        items       : "div.accordion_unit",
        handle      : ".accordion_header",
        cancel      : ".ui-icon",   // not only does this ensure the icon does not sort, it also resets the "cancel" option which prevented inputs from sorting
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

function view_all_categories(view_all_button) {
    var current_tab = $(view_all_button).closest(".tab_content");
    $(current_tab).find(".categories:first .tagit-choice").each(function() {
        $(this).removeClass("ui-state-disabled");
    });
    $(current_tab).find(".accordion_unit").each(function() {
        $(this).show();
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
                    // the addition of the 'true' attribute forces initialization,
                    // even if this dialog is opened multiple times
                    init_widgets(readonlies, $(parent).find(".readonly"), true);
                    init_widgets(buttons, $(parent).find("input.button"), true);
                    init_widgets(helps, $(parent).find(".help_button"), true);
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

    url_root = window.document.location.protocol + "//" + window.document.location.host + "/ajax/customize_subform/";
    //url += "?i=" + subform_id;

    // can't actually use the predefined dialog
    // since I could potentially have multiple instances open at once
    // I need a unique instance each time this fn is called
    //var customize_subform_dialog = $("#customize_subform_dialog");
    var customize_subform_dialog = $(document.createElement("div"));

    $.ajax({
        //url: url,
        url : url_root + "?i=" + subform_id,
        type: "GET",
        cache: false,
        success: function (data) {
            $(customize_subform_dialog).html(data);
            $(customize_subform_dialog).dialog({
                modal: true,
                hide: "explode",
                height: 860,
                width: 1200,
                dialogClass: "no_close",
                title: "Customize Subform",
                open: function () {
                    // apply all of the JQuery code to _this_ dialog
                    var parent = $(customize_subform_dialog);
                    // the addition of the 'true' attribute forces initialization,
                    // even if this dialog is opened multiple times
                    init_widgets(readonlies, $(parent).find("readonly"), true);
                    init_widgets(buttons, $(parent).find("input.button"), true);
                    init_widgets(fieldsets, $(parent).find(".collapsible_fieldset"), true);
                    init_widgets(selects, $(parent).find(".multiselect"), true);
                    init_widgets(accordions, $(parent).find(".accordion").not(".fake"), true);
                    init_widgets(sortable_accordions, $(parent).find(".accordion .accordion_header"), true);
                    init_widgets(accordion_buttons, $(parent).find(".subform_toolbar button"), true);
                    init_widgets(helps, $(parent).find(".help_button"), true);
                    init_widgets(enablers, $(parent).find("enabler"), true);
                    init_widgets(tags, $(parent).find(".tags"), true);
                    init_widgets(tabs, $(parent).find(".tabs"), true);

                },
                buttons: [
                    {
                        text: "save",
                        click: function () {
                            var subform_data = $(this).find("#customize_subform_form").serialize();
                            $.ajax({
                                //url: url,
                                url : url_root + "?i=" + subform_id,
                                type: "POST",  // (POST mimics submi)
                                data: subform_data,
                                cache: false,
                                error: function (xhr, status, error) {
                                    console.log(xhr.responseText + status + error);
                                },
                                success: function (data, status, xhr) {

                                    var msg = xhr.getResponseHeader("msg");
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

                                    var status_code = xhr.status;
                                    if (status_code == 200) {

                                        var parsed_data = $.parseJSON(data);
                                        var subform_customizer_id = parsed_data.subform_customizer_id;
                                        var subform_customizer_name = parsed_data.subform_customizer_name;

                                        var subform_customizer_field = $("select[name='" + subform_customizer_field_name + "']");
                                        if ($(subform_customizer_field).find("option[value='" + subform_customizer_id + "']").length == 0) {
                                            // add this new customizer if it didn't already exist
                                            $(subform_customizer_field).append(
                                                $("<option>", { value: subform_customizer_id }).text(subform_customizer_name)
                                            );
                                        }
                                        $(subform_customizer_field).val(subform_customizer_id)

                                        $(customize_subform_dialog).dialog("close");

                                    }
                                    else {

                                        $(customize_subform_dialog).html(data)
                                        // re-apply all of the JQuery code
                                        var parent = $(customize_subform_dialog);
                                        // the addition of the 'true' attribute forces initialization,
                                        // even if this dialog is opened multiple times
                                        init_widgets(readonlies, $(parent).find("readonly"), true);
                                        init_widgets(buttons, $(parent).find("input.button"), true);
                                        init_widgets(fieldsets, $(parent).find(".collapsible_fieldset"), true);
                                        init_widgets(selects, $(parent).find(".multiselect"), true);
                                        init_widgets(accordions, $(parent).find(".accordion").not(".fake"), true);
                                        init_widgets(sortable_accordions, $(parent).find(".accordion .accordion_header"), true);
                                        init_widgets(accordion_buttons, $(parent).find(".subform_toolbar button"), true);
                                        init_widgets(helps, $(parent).find(".help_button"), true);
                                        init_widgets(enablers, $(parent).find("enabler"), true);
                                        init_widgets(tags, $(parent).find(".tags"), true);
                                        init_widgets(tabs, $(parent).find(".tabs"), true);

                                    }
                                }
                            })
                        }
                    },
                    {
                        text: "Cancel",
                        click: function () {
                            $(customize_subform_dialog).dialog("close");
                        }
                    }

                ],
                close: function () {
                    $(this).dialog("close")
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
};


function sort_accordions(sort_target,sort_key) {

    if (sort_key.indexOf("name")>=0) {
        key_selector = ".accordion_header input[name$='-name']";
    }
    else if (sort_key.indexOf("category")>=0) {
       key_selector = ".accordion_header input[name$='-category_name']";
    }
    else if (sort_key.indexOf("order")>=0) {
       key_selector = ".accordion_header input[name$='-order']";

    }
    else if (sort_key.indexOf("field_type")>0) {
        key_selector = ".accordion_header input[name$='-field_type']";
    }
    else {
        alert("unknown sort key: " + key)
    }

    var sortable_items = $(sort_target).children(".accordion_unit").get();
    sortable_items.sort(function(a,b){
       var a_key = $(a).find(key_selector).val();
       var b_key = $(b).find(key_selector).val();
       if (sort_key.indexOf("order")>=0) {
           // order is an integer comparison; all others are string (default) comparisons
           a_key = parseInt(a_key);
           b_key = parseInt(b_key);
       }
       return (a_key < b_key) ? -1 : (a_key > b_key) ? 1 : 0;
    });

    $.each(sortable_items, function(i, item) {
        $(sort_target).append(item);
    });


};
