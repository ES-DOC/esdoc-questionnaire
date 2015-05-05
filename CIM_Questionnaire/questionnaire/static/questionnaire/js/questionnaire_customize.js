/* functions specific to the customizer */

var STANDARD_TAG_TYPE   = 0;
var SCIENTIFIC_TAG_TYPE = 1;

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

    var tag_widget = element;
    /* note that the value of the comparison string has to match the values in "forms/forms_customize_categories.py#TagTypes" */
    var tag_type = $(tag_widget).attr("name") == "standard_categories" ? STANDARD_TAG_TYPE : SCIENTIFIC_TAG_TYPE;
    var category_form_container = $(tag_widget).nextAll("div.categories_forms");
    var category_forms = $(category_form_container).find("div.category_form");

    var property_forms = $(tag_widget).closest("div.categories").nextAll("div.accordion:first").find("div.form");

    $(tag_widget).tagit({
        allowSpaces : true,
        singleField : true,
        singleFieldDelimiter : "|",
        containment: "parent",  /* prevent overflows; used in conjuction w/ the "containment" option of ".sortable()" below */
        caseSensitive: true,
        allowDuplicates: true,
        afterTagAdded : function(event, ui) {
            var tag = ui.tag;
            var tag_label = $(tag).find("span.tagit-label");
            var tag_name = $(tag_label).text();

            $(tag_label).attr("title", "click to toggle properties belonging to this category");
            /* hide the delete button for standard categories */
            if (tag_type == STANDARD_TAG_TYPE) {
                $(tag).find(".tagit-close").hide();
            }
            /* add an edit button for all categories */
            $(tag_label).before(
                "<a class='tagit-edit' title='edit this category' onclick='edit_tag(this);'>" +
                "<span class='ui-icon ui-icon-pencil'></span>" +
                "</a>"
            );
            $(tag).click(function(event) {
                /* if you really clicked the tag, and not an icon/button on the tag... */
                if ($(event.target).attr("class").indexOf("ui-icon") == -1) {
                    /* toggle its state... */
                    $(this).toggleClass("ui-state-disabled");
                    /* and that of all corresponding properties... */
                    $(this).closest("div.tab_content").find(".accordion_header input.label[name$='category_name']").each(function() {

                        if ($(this).val() == tag_name) {
                            var section = $(this).closest("div.accordion_unit");
                            $(section).toggle();
                        }
                    });
                }
            });

        },
        beforeTagRemoved: function(event, ui) {

            if (tag_type == STANDARD_TAG_TYPE) {

                alert("You shouldn't be deleting standard categories!  You're a very naughty boy!");

            }

            else {

                var tag = ui.tag;
                var tag_label = $(tag).find("span.tagit-label");
                var tag_name = $(tag_label).text();
                var tag_key = slugify(tag_name);

                /* I am _not_ using a dialog box to popup this msg */
                /* b/c JQuery .dialog() is asynchronous and the tag will be removed while waiting for a user response */
                /* instead I am using the JS .confirm() fn which is synchronous */
                var should_delete_tag = confirm("Any properties belonging to this category will become uncategorized.  You cannot undo this operation.  Do you wish to continue?");
                if (should_delete_tag == true) {
                    $.each(category_forms, function(i, category_form) {
                        var form = $(category_form).find("div.category_form_content");
                        var category_name = $(form).find("input[name$='-name']").val();
                        if (category_name == tag_name) {
                            /* 1st marke the category form for deletion */
                            var delete_button = $(form).nextAll("a.delete-row:first");
                            $(delete_button).trigger("click");

                            /* then remove the category from property pull downs */
                            remove_property_categories(property_forms, tag_key, tag_name);

                            return false;  /* break out of the loop */
                        }
                    });
                }
                else {
                    return false;
                }
            }
        }
    });

    // now that the tagit widget has been created we can further customize it...
    var tagit_widget = $(tag_widget).next("ul.tagit:first");

    if (tag_type == SCIENTIFIC_TAG_TYPE) {
        $(tagit_widget).attr("style", "width: 94%;");  /* shorted the widget a bit, to allow room for the "add_tag" button */
    }

    $(tagit_widget).sortable({
        axis: "x",
        items: "li:not(.tagit-new)",
        placeholder: "sortable_item",
        containment: "parent",
        start: function (e, ui) {
            ui.placeholder.height(ui.item.height());
            ui.placeholder.width(ui.item.width());
        },
        stop: function(e, ui) {
            var new_tag_order = $(this).find("li.tagit-choice").map(function() {
                return $(this).find("span.tagit-label").text();
            }).get();
            for (var order=0; order < new_tag_order.length; order++) {
                var tag_name = new_tag_order[order];
                $.each(category_forms, function(i, category_form) {
                   var category_name = $(category_form).find("input[name$='-name']").val();
                   if (category_name == tag_name) {
                       var category_order = $(category_form).find("input[name$='-order']");
                       $(category_order).val(order + 1); /* JS is 0-based, Django is 1-based */
                       return false; /* break out of the inner loop */
                   }
                });
            }
        }

    });

    /* setup how adding new tags is done... */
    /* disable the default way of adding tags */
    $(tagit_widget).find(".tagit-new").hide();
    /* and replace it with this button */
    var add_tag_button = $(tagit_widget).prevAll("button.add_tag:first");
    if (tag_type == STANDARD_TAG_TYPE) {
        /* but not for standard categories, */
        $(add_tag_button).hide();
    }
    else {


        var widget_id = $(element).closest("div.tab_content").closest("div[id^='tab_scientific_properties_']").attr("id");
        var model_key = widget_id.match("tab_scientific_properties_(.*)")[1].split('_');

        $(add_tag_button).button({
            icons: { primary: "ui-icon-circle-plus"},
            text: false
        }).click(function() {
            $(category_form_container).find("a.add-row").trigger("click");
            var new_category_forms = $(category_form_container).find("div.category_form");
            var new_category_form = $(new_category_forms).last();
            var new_category_name = "new category";
            var new_category_order = new_category_forms.length;

            $(tag_widget).tagit("createTag", new_category_name, "added");
            var new_tag = $(tagit_widget).find(".tagit-choice:last");

            /* WHEN DEALING w/ EDITING FORMS I NEED TO CHANGE THE PREFIXES */
            /* BUT HERE IN THE CUSTOMIZER, I DON'T */
            /* I DO, HOWEVER, HAVE TO UPDATE THE VALUES */

            $(new_category_form).find("input[name$='-vocabulary_key']").val(model_key[0]);
            $(new_category_form).find("input[name$='-component_key']").val(model_key[1]);
            $(new_category_form).find("select[name$='-proxy'] option:selected").removeAttr("selected");

            $(new_category_form).find("input[name$='-name']").val(new_category_name);
            $(new_category_form).find("input[name$='-order']").val(new_category_order);

            $(new_category_form).find("input[name$='-loaded']").prop("checked", true);

            edit_tag($(new_tag).find("a.tagit-edit"));  /* simulate clicking the edit button (forces users to change the default name) */

            return false;  /* don't perform the default button action (which would be submitting the form) */
        });

        var prefix = model_key[0] + "_" + model_key[1] + "_" + $(element).attr("name");
        $(category_forms).formset({
            prefix : prefix
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


function remove_property_categories(property_forms, category_key, category_name) {
    $(property_forms).find("select[name$='-category']").each(function() {
        var option = $(this).find("option[value='" + category_key + "']");
        if (option) {
            $(option).remove();
        }
        $(this).trigger("change");
    });
}


function update_property_categories(property_forms, old_category_key, new_category_key, new_category_name) {

    $(property_forms).find("select[name$='-category']").each(function() {
        var option = $(this).find("option[value='" + old_category_key + "']");
        if (option.length) {
            option.attr("value", new_category_key);
            option.text(new_category_name);
        }
        else {
            $(this).append("<option value='" + new_category_key + "'>" + new_category_name + "</option>");
        }
        $(this).trigger("change");
    });
}


function edit_tag(edit_tag_icon) {

    var tag_widget = $(edit_tag_icon).closest(".tagit");
    var tag_label = $(edit_tag_icon).next(".tagit-label");
    var tag_name = $(tag_label).text();
    var tag_key = slugify(tag_name);
    /* note that the value of the comparison string has to match the values in "forms/forms_customize_categories.py#TagTypes" */
    var tag_type = $(tag_widget).prev("input.tags").attr("name") == "standard_categories" ? STANDARD_TAG_TYPE : SCIENTIFIC_TAG_TYPE;

    var category_forms = $(tag_widget).nextAll("div.categories_forms").find("div.category_form");
    $.each(category_forms, function(i, category_form) {
        var form = $(category_form).find("div.category_form_content");
        var form_fields = $(form).find("input,select,textarea,button");
        var category_name = $(form).find("input[name$='-name']").val();

        if (category_name == tag_name) {

            var url = window.document.location.protocol + "//" + window.document.location.host + "/api/customize_category/";
            url += $(tag_widget).prev("input.tags").attr("name"); /* this gives the type: standard or scientific */
            url += "/";  /* trailing slash is required to prevent RuntimeError; alternatively, could set APPEND_SLASH to False in Django settings */

            var edit_dialog = $("#edit_dialog");

            $.ajax({
                url: url,
                type: "GET",
                cache: false,
                data: $(form_fields).serializeArray(),
                success: function(data) {
                    $(edit_dialog).html(data);
                    $(edit_dialog).dialog("option", {
                        autoOpen: false,
                        height: 400,
                        width: 600,
                        dialogClass: "no_close",
                        title: "Edit Category",
                        open: function() {
                            var parent = $(edit_dialog);
                            init_widgets(readonlies, $(parent).find(".readonly"), true);
                            init_widgets(helps, $(parent).find(".help_button"), true);
                            init_widgets(buttons, $(parent).find("input.button"), true);
                        },
                        buttons: {
                            ok: function() {
                                $.ajax({
                                    url: url,
                                    type: "POST", /* (POST mimics submit) */
                                    data: $(edit_dialog).find("input,select,textarea").serializeArray(),
                                    cache: false,
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
                                            $.each(parsed_data, function (key, value) {
                                                /* TODO: WHY CAN'T I RE-USE $(form_fields) HERE? */
                                                /*var field = $(form_fields).("[name$='-" + key + "']")*/
                                                var field = $(form).find("input[name$='-" + key + "'],select[name$='-" + key + "'],textarea[name$='-" + key + "']");
                                                if ($(field).is(":checkbox")) {
                                                    $(field).prop("checked", value);
                                                }
                                                else {
                                                    $(field).val(value);
                                                }
                                                if (key == "name") {
                                                    $(tag_label).text(value);
                                                }

                                            });

                                            if (tag_type = SCIENTIFIC_TAG_TYPE) {
                                                var property_forms = $(tag_widget).closest("div.categories").nextAll("div.accordion:first").find("div.form");
                                                update_property_categories(property_forms, tag_key, parsed_data.key, parsed_data.name);
                                            }

                                            $(edit_dialog).dialog("close");
                                        }
                                        else {
                                            $(edit_dialog).html(data);
                                            //var parent = $(edit_dialog);
                                            //init_widgets(readonlies, $(parent).find(".readonly"), true);
                                            //init_widgets(helps, $(parent).find(".help_button"), true);
                                            //init_widgets(buttons, $(parent).find("input.button"), true);
                                        }
                                    },
                                    error: function (xhr, status, error) {
                                        console.log(xhr.responseText + status + error)
                                    }
                                });
                            }
                            // don't allow canceling the dialog
                            // this requires users to change the name of new categories (since the ok button forces validation)
                            //},
                            //cancel: function() {
                            //    $(edit_dialog).dialog("close");
                            //}
                        }
                    }).dialog("open");
                },
                error: function(xhr, status, error) {
                    console.log(xhr.responseText + status + error)
                }
            });

            return false; /* break out of the loop */
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

    var url_root = window.document.location.protocol + "//" + window.document.location.host + "/ajax/customize_subform/";

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
                    init_widgets(enablers, $(parent).find("enabler"), true);
                    init_widgets(accordions, $(parent).find(".accordion").not(".fake"), true);
                    init_widgets(sortable_accordions, $(parent).find(".accordion .accordion_header"), true);
                    init_widgets(accordion_buttons, $(parent).find(".subform_toolbar button"), true);
                    init_widgets(tags, $(parent).find(".tags"), true);
                    init_widgets(tabs, $(parent).find(".tabs"), true);
                    init_widgets(buttons, $(parent).find("input.button"), true);
                    init_widgets(multiselects, $(parent).find(".multiselect"), true);
                    init_widgets(helps, $(parent).find(".help_button"), true);
                    init_widgets(readonlies, $(parent).find("readonly"), true);
                    init_widgets(fieldsets, $(parent).find(".collapsible_fieldset"), true);
                    $(parent).find("button.customize_subform").button({
                        icons: {prmary: "ui-icon-extlink"},
                        text: true
                    });
                },
                buttons: [
                    {
                        text: "save",
                        click: function () {
                            var subform_data = $(this).find("#customize_subform_form").serialize();
                            $.ajax({
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
                                        // reapply all of the JQuery code to the dialog
                                        var parent = $(customize_subform_dialog);
                                        // the addition of the 'true' attribute forces initialization,
                                        // even if this dialog is opened multiple times
                                        init_widgets(enablers, $(parent).find("enabler"), true);
                                        init_widgets(accordions, $(parent).find(".accordion").not(".fake"), true);
                                        init_widgets(sortable_accordions, $(parent).find(".accordion .accordion_header"), true);
                                        init_widgets(accordion_buttons, $(parent).find(".subform_toolbar button"), true);
                                        init_widgets(tags, $(parent).find(".tags"), true);
                                        init_widgets(tabs, $(parent).find(".tabs"), true);
                                        init_widgets(buttons, $(parent).find("input.button"), true);
                                        init_widgets(multiselects, $(parent).find(".multiselect"), true);
                                        init_widgets(helps, $(parent).find(".help_button"), true);
                                        init_widgets(readonlies, $(parent).find("readonly"), true);
                                        init_widgets(fieldsets, $(parent).find(".collapsible_fieldset"), true);
                                        $(parent).find("button.customize_subform").button({
                                            icons: {prmary: "ui-icon-extlink"},
                                            text: true
                                        });
                                    }
                                }
                            })
                        }
                    },
                    {
                        text: "cancel",
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
