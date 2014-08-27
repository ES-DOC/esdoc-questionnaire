/* BEGIN enable ajax access to the same domain */

// see https://docs.djangoproject.com/en/1.6/ref/contrib/csrf/#ajax for more info

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
};

function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
};

var csrftoken = getCookie('csrftoken');

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

/* END enable ajax access to the same domain */

/* functions to initialize jquery widgets */
/* (widgets specific to edit/view or customize forms are defined in their respective js files) */

/*  there are two different ways to initialize widgets:
    immediately (all at once) via init_widget
    or on the "show" event via init_widget_on_show
    both of these fns take an initialization fn and only run than fn if it hasn't run before
    the distinction between these fns is especially relevant for subforms; any new JQuery widgets
    in  a subform must be initialized but a previously called global initializtion (via init_widget)
    can interfere w/ additional initializations.  Therefore, it makes sense to use init_widget_on_show
    with subforms.
 */

function init_widgets_on_show(init_fn, elements) {

    $(elements).each(function() {
        var initialized_widget_class_name = "initialized_" + init_fn.name;
        $(this).on("show", function() {
            if (! $(this).hasClass(initialized_widget_class_name) ) {
                init_fn(this);
                $(this).addClass(initialized_widget_class_name);
            }
        });
    });

}

function init_widgets(init_fn, elements, force_init) {

    force_init = typeof force_init !== 'undefined' ? force_init : false;

    $(elements).each(function() {
        var initialized_widget_class_name = "initialized_" + init_fn.name;
        if (! $(this).hasClass(initialized_widget_class_name) || (force_init)) {
            init_fn(this);
            $(this).addClass(initialized_widget_class_name)
        }
    });

}

function users(element) {
    $(element).find("a.button").button({});
}

function readonlies(element) {
   $(element).closest("tr.field").find("input,textarea,select,button,span").each(function() {
       $(this).addClass("ui-state-disabled");
       $(this).prop("disabled",true);
   });
}

function accordion_buttons(element) {

    if ($(element).hasClass("expand")) {
        $(element).button({
            icons: {primary: "ui-icon-circle-triangle-s"},
            text: true
        }).click(function (event) {
            var accordion = $(event.target).closest(".subform_toolbar").nextAll(".accordion:first");

            // can't use the built-in plugin "active=all" option
            // b/c accordions are wrapped in ".accordion_content"
            // (to allow sorting in customizer and dynamic adding/removing in editor)
            $(accordion).children(".accordion_unit").each(function () {
                var header = $(this).find(".accordion_header:first");
                if (!$(header).hasClass("open_accordion")) {
                    $(header).click();
                }
            });
        });
    }

    if ($(element).hasClass("collapse")) {
        $(element).button({
            icons: {primary: "ui-icon-circle-triangle-n"},
            text: true
        }).click(function (event) {
            var accordion = $(event.target).closest(".subform_toolbar").nextAll(".accordion:first");

            // as above, can't use the built-in plugin "active=none" option
            $(accordion).children(".accordion_unit").each(function () {
                var header = $(this).find(".accordion_header:first");
                if ($(header).hasClass("open_accordion")) {
                    $(header).click();
                }
            });
        });
    }

    if ($(element).hasClass("sort")) {
        $(element).button({
            icons: { primary: "ui-icon-arrowthick-2-n-s"},
            text: true
        }).click(function (event) {
            var menu = $(this).next(".sort_by").show().position({
                my: "left top",
                at: "left bottom",
                of: this
            });
            $(document).one("click", function () {
                // attaches a handler for "click" on the document;
                // any click hides the menu
                $(menu).hide();
            });
            return false;
        });

        $(element).find(".sort_by").each(function () {
            $(this).menu().width("8em").hide();
            $(this).click(function (event) {
                var sort_key = $(event.target).attr("name");
                var sort_target = $(event.target).closest(".tab_content").find(".accordion:first");
                sort_accordions(sort_target, sort_key);
                $(event.target).closest(".sort_by").hide();     // hide the sort_by menu
                event.preventDefault();                         // don't actually follow the menu link (one of these is bound to work)
                return false;                                   // don't actually follow the menu link (one of these is bound to work)
            });
        });
    }

}

function buttons(element) {
    // submit buttons...
    $(element).button({});
}

function enablers(element) {
    $(element).trigger("change");
}

function dates(element) {
    $(element).datepicker({
        changeYear: true,
        showButtonPanel: false,
        showOn: 'button'
    }).next("button").button({
        icons: { primary: "ui-icon-calendar" },
        text: false
    }).attr("title", "click to select date");
}

function xdates(parent) {
    $(parent).find(".date,.datetime").each(function() {
        var field_id = $(this).attr("id");
        /* clear any previous setup, to ensure widget is bound to the current input element */
        //$(this).next("button").button("destroy");
        //$(this).datepicker('destroy');
        if (! $(this).hasClass("hasDatepicker")) {
            $(this).datepicker({
                //altField: "#"+field_id,
                changeYear: true,
                showButtonPanel: false,
                showOn: 'button'
            }).next("button").button({
                icons: { primary: "ui-icon-calendar" },
                text: false
            });
        };
    });

    $(".ui-datepicker-trigger").mouseover(function () {
        $(this).css('cursor', 'pointer');
    });
    $(".ui-datepicker-trigger").attr("title", "click to select date");

};

function fieldsets(element) {
    $(element).addClass("expanded");
    $(element).find("legend:first").click(function() {
        $(this).next(".collapsible_fieldset_content").slideToggle( "fast", function() {
            var fieldset = $(this).parent("fieldset");
            $(fieldset).toggleClass("collapsed");
            $(fieldset).toggleClass("expanded");
        });
    });
}

function tabs(element) {
    $(element).tabs({
    });
}


function selects(element) {
    $(element).multiselect({
       autoOpen  : false,
       multiple  : ($(this).is("[multiple]")) ? true : false,
       sortable  : false,
       numToShow : 1
    });
}

function accordions(element) {

    $(element).multiOpenAccordion({
        active : false,   // this _should_ hide all panes, but there is a known bug [http://code.google.com/p/jquery-multi-open-accordion/issues/detail?id=15] preventing this
        tabShown : function(event,ui) {
            var active_tab      = ui["tab"];
            var active_content  = ui["content"];
            if ($(active_tab).hasClass("sorting")) {
                // if the accordion content is being opened just b/c it was clicked during sorting,
                // then cancel the show event and reset the relevant styles
                $(active_content).hide();
                $(active_tab).removeClass("ui-state-active sorting");
                $(active_tab).addClass("ui-state-default");
                var active_tab_icon = $(active_tab).find(".ui-icon");
                $(active_tab_icon).removeClass("ui-icon-triangle-1-s");
                $(active_tab_icon).addClass("ui-icon-triangle-1-e");
            }
            else {
                if (! $(active_tab).hasClass("ui-state-error")) {
                    $(active_tab).addClass("open_accordion");
                }
            }
            // NO LONGER NEEDED SINCE INTRODUCTION OF init_widgets_on_show FN
            //init_widgets(selects,active_content);

        },
        tabHidden : function(event,ui) {
            var active_tab      = ui["tab"];
            var active_content  = ui["content"];
            $(active_tab).removeClass("open_accordion");
        }
    });
    $(element).find(".ui-accordion-content").hide(); // see comment about "active : false" above

}

function helps(element) {
   $(element).mouseover(function() {
       $(this).css("cursor","pointer");
   });
   $(element).hover(
      function() {
          $(this).children(".ui-icon-info").addClass("hover-help-icon");
      },
      function() {
          $(this).children(".ui-icon-info").removeClass("hover-help-icon");
      }
   );
   $(element).click(function() {
       /* I escape any periods that may be in the ids (unlikely) so that JQuery doesn't interepret them as class selectors */
       var id = "#" + $(this).attr("id").replace(/(:|\.)/g,'\\$1');

       var x = $(this).offset().left - $(document).scrollLeft();
       var y = $(this).offset().top - $(document).scrollTop();

       var description = $(this).find(".help_description:first");
       var title = $(description).attr("title");
       var text = $(description).html();
       $("#help_dialog").html(text);
       $("#help_dialog").dialog("option",{title: title, position: [x,y], height: 200, width: 400}).dialog("open");
       return false;
   })
}

function init_dialogs(parent) {
    /*
    $("#help_dialog").dialog({
        autoOpen:false,hide:'explode',modal:true
    });
    $("#confirm_dialog").dialog({
        autoOpen:false,hide:'explode',modal:true
    });
    $("#add_dialog").dialog({
        autoOpen:false,hide:'explode',modal:true
    });
    $("#remove_dialog").dialog({
        autoOpen:false,hide:'explode',modal:true
    });
    $("#edit_dialog").dialog({
       autoOpen:false,hide:'explode',modal:true
    });
    */
    $(".hidden_dialog").dialog({
       autoOpen:false,hide:'explode',modal:true
    });
}

function init_errors(parent) {
    $(parent).find(".error_wrapper").each(function() {
       render_error($(this));
    });
}

function render_error(error) {
    // render fields...
    $(error).parents(".field:first").find("input,textarea,select").addClass("ui-state-error");
    
    // render fieldsets...
    $(error).parents(".collapsible_fieldset").each(function() {
        $(this).addClass("error")
    });

    // render accordions...
    $(error).parents(".accordion_content").each(function() {
        $(this).prev(".accordion_header").addClass("ui-state-error");
    });
    
    // render tabs...
    $(error).parents(".tab_content").each(function() {
        var tab_id = $(this).parent(".ui-tabs-panel").attr("id");
        $("a[href='#"+tab_id+"']").closest("li").addClass("ui-state-error");
    });

    // render treeview nodes...
}
    
function render_msg(msg) {
    $(msg).find("div.msg").each(function() {
        $(this).dialog({
            modal       : true,
            hide        : "explode",
            height      : 200,
            width       : 400,
            dialogClass : "no_close",
            buttons : {
                OK: function() {
                    $(this).dialog("close");
                }
            }
       });
    });
}

function enable(source,enabling_value,targets) {

    var source_value_matches = false;
    if ($(source).attr("type") == "checkbox") {
        if ( ( ( enabling_value.toLowerCase()=="true" ) && ( $(source).is(":checked") ) )  || ( ( enabling_value.toLowerCase()=="false" ) && !( $(source).is(":checked") ) ) ) {
            source_value_matches = true;
        }
    }
    /*
     * TODO: HANDLE MULTISELECTS *
    else if ( ($(source).prop("tagName").toLowerCase()=="select") && ($(source).attr("multiple"))) {
        alert("I still need to write a handler in enable() for multiselects");
    }
    */
    else {
        if ($(source).val() == enabling_value) {
            source_value_matches = true;
        }
    }

    for (var i = 0; i < targets.length; i++) {
        var selector = ".field[name$='" + targets[i] + "']";
        var target_container = $(source).closest(".form").find(selector)
               
        if (source_value_matches) {
            $(target_container).find("input,textarea,select,button,span").each(function() {
                $(this).removeClass("ui-state-disabled");
                $(this).prop("disabled",false);
            });
        }
        else {
            $(target_container).find("input,textarea,select,button,span").each(function() {
                $(this).addClass("ui-state-disabled");
                $(this).prop("disabled",true);
            });
        }
    }

};

function copy_value(source,target_name) {
    var source_value;
    if ($(source).prop("tagName").toLowerCase()=="select") {
        source_value = $(source).find("option:selected").html();
    }
    else {
        source_value = $(source).val();
    }
    var target = $("*[name='"+target_name+"']");
    $(target).val(source_value);
}

function restrict_options_bak(source,target_names) {

    restrictions = [];
    $(source).find("option:selected").each(function() {
        restrictions.push($(this).val());
    });

    for (var i=0; i<target_names.length; i++) {
        // TODO: THIS SHOULD WORK FOR MORE THAN JUST SELECT FIElDS
        var selector = "select[name$='" + target_names[i] + "']";
        var target = $(source).closest("div.form").find(selector);
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
            $(target).find("option[value='"+this+"']:first").remove();
        });
        // add everything in restrictions and not in options
        $(in_restrictions_but_not_options).each(function() {
            var option = $(source).find("option[value='"+this+"']:first");
            $(target).append($("<option>").attr("value",this).text($(option).text()));
        });

    }
}


function slugify(string) {
    return string.toLowerCase().replace(/[^\w ]+/g,'').replace(/ +/g,'-');
}

function update_field_names(form,old_prefix,new_prefix) {
    /* for every field in form change the name and id from "old_prefix" to "new_prefix" */

    $(form).find("input,select,textarea,label").each(function() {
        var _id = $(this).attr("id");
        var _name = $(this).attr("name");
        var _for = $(this).attr("for"); /* this is for labels w/in the multiselect widget */

        if (_id) {
            $(this).attr("id",_id.replace(old_prefix,new_prefix));
        }
        if (_name) {
            $(this).attr("name",_name.replace(old_prefix,new_prefix));
        }
        if (_for) {
            $(this).attr("for",_for.replace(old_prefix,new_prefix));
        }

    });
};

function populate_form(form,data) {

    $.each(data,function(key,value) {

        var field_selector = "*[name='" + key + "']";
        var field = $(form).find(field_selector);
        if (field.length) {

            var field_type = $(field).prop("tagName").toLowerCase();

            // field can either be input, select (including multiple select), or textarea
            // TODO: WHAT ABOUT MULTISELECT WIDGETS?

            if (field_type == "input") {
                $(field).val(value);
            }

            else if (field_type == "textarea") {
                $(field).val(value);
            }

            else if (field_type == "select") {
                $(field).val(value);
            }
        }

    });

};

