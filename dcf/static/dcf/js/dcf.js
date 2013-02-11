/* top-level dcf JS code */

/* TODO: EVENTUALLY, I'LL MOVE TO SOMETHING LIKE BACKBONE TO RE-ORGANIZE MY JS  */
/* IN THE MEANTIME, I HAVE SEPARATED THEM OUT INTO MULTIPLE FILES,              */
/* AND INCLUDED RELEVANT FNS FROM EACH ONE IN A VAR (LIKE NAMESPACING)          */
/* THIS ISN'T PERFECT, BUT IT MAKES LIFE A BIT EASIER                           */

function loadJS(js_path) {
    // this fn loads another script
    // I am not useing the getScript() fn, b/c that does not cache results
    // instead I just make a standard AJAX call, but set "cache" to "true"
    options = { dataType : "script", cache : true, url : js_path}
    return $.ajax(options).done(function(script,status) {
        console.log(status);
    });
};

// code explicitly dealing w/ the customization form
loadJS(JS_PATH+"/dcf_customize.js");
// code explicitly dealing w/ the editing form
loadJS(JS_PATH+"/dcf_edit.js");
// code explicitly dealing w/ the interplay between fields
loadJS(JS_PATH+"/dcf_fields.js");
// code explicitly dealing w/ initializing widgets as they appear
loadJS(JS_PATH+"/dcf_initialize.js");

/* global vars */
var VERSION
var PROJECT
var MODEL

/* main fn in each dcf js file */
/* it sets up all of the static JQuery widgets */
/* this top-level fn also calls enableDCF for all the other js files */
function enableDCF() {

    $(function() {

        /*************************/
        /* setup any global vars */
        /*************************/
        VERSION = $("div.global_vars span[name='version']").text();
        PROJECT = $("div.global_vars span[name='project']").text();
        MODEL   = $("div.global_vars span[name='model']").text();

        /************************/
        /* setup JQuery widgets */
        /************************/
        
        /* enable the dialog boxes */
        /* (the msg dialog box is explicitly setup in the "dcf_base" template) */
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
        
        /* enable collapsible fieldsets */
        $(".coolfieldset").coolfieldset({speed:"fast"});
        // if I need to open/close a fieldset use the following code:
        // $(".coolfieldset[name='whatever'] legend").trigger("click");

        /* enable tabs */
        $(".tabs").tabs();
        
        /* change the look and feel of a disabled field */
        /* sets the "readonly" class on that field's label & the actual field */
        /* CSS does the rest */
        $(".readonly").each(function() {
            // works for fields in a table (tr) or a div
            $(this).closest("tr.field,div.field").find(".field_label,.field_value").addClass("readonly");
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
                   
                   if($(activeContent).attr("class").indexOf("initialized")==-1) {
                       initialize_section(activeContent);
                       $(activeContent).addClass("initialized");
                   }


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
                    var order_input = $(this).find("input[name$='-order']")
                    $(order_input).val(i+1);
                    $(order_input).trigger("change");
                    //$(this).find("input[name$='-order']").val(i+1);

                });
            }
            /* TODO: JQUERY DOCUMENTATION IMPLIES SOME MORE CODE HERE TO HANDLE IE BUG */
        });

        
        $(".dropdownchecklist").multiselect({
            autoOpen : false,
            header : false,
            minWidth : 500
        });

        /********************************************/
        /* now call the enablers for other js files */
        /********************************************/
        CUSTOMIZE.enableDCF();
                
    });
};

/* initially, a lot of the form elements are hidden */
/* (inside accordions or behind inactive tabs) */
/* so this fn gets called whenever a new section is displayed */
/* it winds up repeating some of the functionality of enableJQueryWidgets below */
function initialize_section(parent) {
    // dropdownchecklists...
    $(parent).find(".dropdownchecklist").multiselect({
        autoOpen : false,
        header : false,
        minWidth : 500
    });
};

/* returns a Django Form serialized into the specified format
 * (currently only JSON is supported; can't think why I'd need another format */
function serialize_form(form,format) {
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
           var selector = ".field_value[name='" + targetName + "']";
           // the target can either be an <input> or a <select>
           // TODO: CAN IT BE ANYTHING ELSE?
           var target = $(source).closest(".form").find(selector).find("input,select");
           var targetType = $(target).attr("type");
           if (targetType=="checkbox") {
               if (targetValue.toLowerCase()=="true") $(target).attr('checked', true);
               if (targetValue.toLowerCase()=="false") $(target).attr('checked', false);
           }
           // TODO: ADD MORE CASES FOR OTHER TYPES OF TARGET FIELDS
           else {
               alert("I don't know what to in the function 'link()' with a target of type '" + targetType + "'.");
           }
       }
   }
};


/* toggles the visibility of a set of target fields
 * based on the value of the source field
 * (targets must be in same form/subform)
 */
function enable(source,enablingValue,targets) {
    var sourceValueMatches = false;
    var sourceType = $(source).attr("type");
    if (sourceType == "checkbox") {
        if ( ( ( enablingValue.toLowerCase()=="true" ) && ( $(source).is(":checked") ) )  || ( ( enablingValue.toLowerCase()=="false" ) && !( $(source).is(":checked") ) ) ) {
            sourceValueMatches = true;
        }
    }
    // TODO: ADD MORE CASES FOR OTHER TYPES OF SOURCE FIELDS
    else {
        alert("I don't know what to in the function 'enable()' with a source of type '" + sourceType + "'.");
    }

    for (var i = 0; i < targets.length; i++) {
        var selector = "*[name='" + targets[i] + "']";
        var target = $(source).closest(".form").find(selector).filter("input,select,button");
        var targetType = $(target).prop("tagName").toLowerCase();

        if (targetType=="button") {
            if (sourceValueMatches) $(target).button("enable");
            else $(target).button("disable");
        }
        // TODO: ADD MORE CASES FOR OTHER TYPES OF TARGET FIELDS
        else {
           alert("I don't know what to in the function 'enable()' with a target of type '" + targetType + "'.");
        }
    }

};

function set_label(item,label_name) {
    var selector = "span.label[name='"+label_name+"']"
    var label = $(item).closest(".accordion-content").prev(".accordion-header").find(selector);
    var input_type = $(item).prop("tagName").toLowerCase();
    if (input_type=="select") {
        var input_val = $(item).find("option:selected");
        var new_text = (input_val=="") ? "None" : input_val
    }
    else if (input_type=="input") {
        var input_val = $(item).val();
        var new_text = (input_val=="") ? "None" : input_val
    }

    
    //var newText = ($(item).val()) ? $(item).find("option:selected").text() : "None";
    $(label).text( new_text );
};
