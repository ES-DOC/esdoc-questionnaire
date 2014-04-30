/* functions to initialize JQuery widgets */

function init_widget(init_fn,parent,force_init) {
    force_init = typeof force_init !== 'undefined' ? force_init : false;
    
    initialized_class_name = "initialized_"+init_fn.name;

    // check if we've already initialized this widget for this parent element
    if ($(parent).hasClass(initialized_class_name) && !(force_init)) {
        // (quit if we have)
        return;
    }

    // initialize this widget
    init_fn(parent);
    
    // record that we initialized this widget,
    // so we don't needlessly try to initialize it again
    $(parent).addClass(initialized_class_name);
}

function users(parent) {
    $(parent).find("#user a").button();
}

function readonlies(parent) {
    $(parent).find(".readonly").each(function() {
       $(this).closest("tr.field").find("input,textarea,select,button,span").each(function() {
           $(this).addClass("ui-state-disabled");
           $(this).prop("disabled",true);
       });
    });
}

function buttons(parent) {
    // standard buttons...
    $(parent).find("button,.button").button();

    // buttons for manipulating accordions...
    $(parent).find(".subform_toolbar button.expand").button({
         icons : {primary: "ui-icon-circle-triangle-s"},
         text : true
    }).click(function(event){
        var accordion = $(event.target).closest(".subform_toolbar").nextAll(".accordion:first");

        if ($(accordion).hasClass("ui-sortable")) {
            // I have to do this manually (rather than w/ the active:all option)
            // b/c each accordion is wrapped in 'accordion_content' (to allow sorting)
            $(accordion).children(".accordion_unit").each(function() {
                var header = $(this).find(".accordion_header:first");
                if (! $(header).hasClass("open_accordion")) {
                    $(header).click();
                }
            });
        }
        else {
            $(accordion).multiOpenAccordion("option","active","all");
        }

    });
    $(parent).find(".subform_toolbar button.collapse").button({
         icons : {primary: "ui-icon-circle-triangle-n"},
         text : true
    }).click(function(event){
        var accordion = $(event.target).closest(".subform_toolbar").nextAll(".accordion:first");

        if ($(accordion).hasClass("ui-sortable")) {
            // I have to do this manually (rather than w/ the active:none option)
            // b/c each accordion is wrapped in 'accordion_content' (to allow sorting)
            $(accordion).children(".accordion_unit").each(function() {
                var header = $(this).find(".accordion_header:first");
                if ($(header).hasClass("open_accordion")) {
                    $(header).click();
                }
            });
        }
        else {
            $(accordion).multiOpenAccordion("option","active","none");
        }
    });
    $(parent).find(".subform_toolbar button.sort").button({
        icons : { primary : "ui-icon-arrowthick-2-n-s"},
        text : true
    }).click(function(event){
        var menu = $(this).next(".sort_by").show().position({        
            my : "left top",
            at : "left bottom",
            of : this
        });
        $(document).one("click",function() {
            // attaches a handler for "click" on the document;
            // any click hides the menu
            $(menu).hide();
        });
        return false;

    });
    $(parent).find(".sort_by").each(function() {
        $(this).menu().width("8em").hide();
        $(this).click(function(event){
            var sort_key = $(event.target).attr("name");
            alert("TODO: write handler for " + sort_key);
            $(event.target).closest(".sort_by").hide();     // hide the sort_by menu
            event.preventDefault();                         // don't actually follow the menu link (one of these is bound to work)
            return false;                                   // don't actually follow the menu link (one of these is bound to work)
        });
    });
}

function enablers(parent) {
    $(parent).find(".enabler").trigger("change");
}

function fieldsets(parent) {
    $(parent).find(".collapsible_fieldset").addClass("expanded");
    $(parent).find(".collapsible_fieldset legend").click(function() {
        $(this).next(".collapsible_fieldset_content").slideToggle( "fast", function() {
            var fieldset = $(this).parent("fieldset");
            $(fieldset).toggleClass("collapsed");
            $(fieldset).toggleClass("expanded");
        });
    });
}

function tabs(parent) {
    $(parent).find(".tabs").each(function() {
        $(this).tabs({
            activate : function(event,ui) {
                console.log("should I initialize this container?");
            }
        });
    });
}

function selects(parent) {
    $(parent).find(".multiselect").each(function() {
        $(this).multiselect({
           autoOpen  : false,
           multiple  : ($(this).is("[multiple]")) ? true : false,
           sortable  : false,
           numToShow : 1
        });
    });
}

function accordions(parent) {
    $(parent).find(".accordion").each(function() {
        $(this).multiOpenAccordion({
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
                init_widget(selects,active_content);

            },
            tabHidden : function(event,ui) {
                var active_tab      = ui["tab"];
                var active_content  = ui["content"];
                $(active_tab).removeClass("open_accordion");
            }
        });
        $(this).find(".ui-accordion-content").hide(); // see comment about "active : false" above

    });
}

function helps(parent) {
    $(parent).find(".help_button").each(function(){
       $(this).mouseover(function() {
           $(this).css("cursor","pointer");
       });
       $(this).hover(
          function() {
              $(this).children(".ui-icon-info").addClass("hover-help-icon");
          },
          function() {
              $(this).children(".ui-icon-info").removeClass("hover-help-icon");
          }
       );
       $(this).click(function() {
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
    });
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