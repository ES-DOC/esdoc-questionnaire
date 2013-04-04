/*
#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
*/

/* custom js for the django_cim_forms application */

///////////////////////

var form_to_add_to = ""
var guid_to_add_to = ""
var model_to_add_to = ""
var app_to_add_to = ""
var field_to_add_to = ""

var id_to_add = ""
var model_to_add = ""
var form_to_add = ""
var button_to_add_form = ""

var form_to_remove_from = ""
var guid_to_remove_from = ""
var model_to_remove_from = ""
var app_to_remove_from = ""
var field_to_remove_from = ""

var id_to_remove = ""
var form_to_remove = ""
var button_to_remove_form = ""

/* re-define indexOf incase it's not supported */
/* (as with IE 8.0) */
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(obj, start) {
         for (var i = (start || 0), j = this.length; i < j; i++) {
             if (this[i] === obj) { return i; }
         }
         return -1;
    }
}

/* checks the value of a field (toggler) against an associative array (stuffToToggle)
 * which specifies other fields to toggle based on value */
function toggleStuff(toggler,stuffToToggle) {
    var thisField = $(toggler).parent("div.field");
    var fieldType = $(toggler).attr("type");

    /* TODO: ADD MORE CASES FOR CONDITIONAL ASSIGNMENT (RADIO BOXES, ETC.) */
    var val = (fieldType=="checkbox") ? String($(toggler).is(":checked")) : $(toggler).val();
    
    for (var value in stuffToToggle) {
        var stuff = stuffToToggle[value]
        if (value==val) {
            for (var i=0; i<stuff.length; i++) {
                var selector = "div.field[name='"+stuff[i]+"']";    // look in fields
                $(thisField).find(selector).show();                 // look in descendants
                $(thisField).siblings(selector).show();             // and siblings
                selector = "fieldset[name='"+stuff[i]+"']";         // look in subforms
                $(thisField).find(selector).show();                 // look in descendants
                $(thisField).siblings(selector).show();             // and siblings
            }
        }
        else {
            for (var i=0; i<stuff.length; i++) {
                var selector = "div.field[name='"+stuff[i]+"']";    // look in fields
                $(thisField).find(selector).hide();                 // look in descendants
                $(thisField).siblings(selector).hide();             // and siblings
                selector = "fieldset[name='"+stuff[i]+"']";         // look in subforms
                $(thisField).find(selector).hide();                 // look in descendants
                $(thisField).siblings(selector).hide();             // and siblings
            }
        }
    }
};

/* Fn called whenever a properties details changes
 * it updates the (accordion) title of that property to reflect those changes
 * a similar Django version of this function is called upon initial loading
 */
function setPropertyTitle(propertyFieldWidget) {

    var name = $(propertyFieldWidget).parents("div.accordion-content:first").find("div.field[name='longName']").find("input").val();
    var valueField = $(propertyFieldWidget).parents("div.field[name='value']:first");
    var isCustom = $(propertyFieldWidget).parents("div.accordion-content:first").hasClass("custom-property");

    /* slightly more complex version replaces this version which didn't take into account "other" fields */
    /*
    var value = $(propertyValue).children("option").filter(":selected").map(function () {
        return $(this).text();
    }).get().join('|');
    */

    var value = ""
    if (isCustom) {
        value = $(valueField).find("input").val();
    }
    else {
        value = $(valueField).find("option").filter(":selected").map(function() {
            if ($(this).val() == "OTHER") {
                return "OTHER: " + $(valueField).find("input").val();
            }
            else {
                return $(this).text();
            }
        }).get().join(" | ");
    }

    var accordionHeader = $(propertyFieldWidget).parents("div.accordion-content:first").prev(".accordion-header");
    var title = name + ": " + value + " ";
    $(accordionHeader).find("a").text(title);
    
};

/* populate a specific form
 * w/ specific (JSON) data */
function populate(data, form) {
    
    $.each(data, function(key, value){
        if (key=='pk') {
           
            //$(form).find(".field > [name$='id']:first").val(value[key]);
            $(form).find("input[name$='-id']:first").val(value);
            
        }
        if (key=='fields') {
            for (key in value) {
                if (value.hasOwnProperty(key)) {                   
                    // match all elements with the name of the key (that are children of field)
                    var selector = ".field > [name$='"+key+"']:first";
                    $(form).find(selector).val(value[key]);

                    // of course, this could be an enumeration...
                    // (I can tell by the presence of "|" and/or "||" in the string)
                    // in that case, the above selector would not have matched
                    // and I have to parse out the value and assign it to "<key>_0" & "<key>_1" as appropriate
                    if (String(value[key]).indexOf("|")!=-1) {
                        var enumerationValue = String(value[key]).split("|");
                        var selector0 = ".field > [name$='"+key+"_0']:first";
                        $(form).find(selector0).val(enumerationValue[0]);
                        var selector1 = ".field > [name$='"+key+"_1']:first";
                        $(form).find(selector1).val(enumerationValue[1]);
                    }
                    // TODO: DO THE SAME FOR ENUMERATIONS WHERE MULTI=TRUE

            
                    
                }
            }
        }
    });
};


function resizeFields(parent) {
    // resizes atomic fields to use all available space
    // have to do this dynamically b/c these fields are
    // potentially hidden by tabs and/or accordions
    // this function gets called the 1st time a tab or accordion header is shown
    var margin = 4;
    var padding = 4;
    $(parent).find(".atomic:not(.datepicker, .disabled, .readonly)").each(function(index,value){
       var parentDiv = $(this).closest("div.field");
       var labelSpan = $(this).prev("span.field-label:first");
       $(this).width($(parentDiv).width() - $(labelSpan).width() - (8.0 * (margin + padding)));       
    });
};

function repositionFields(parent) {
    // repositions "enumeration-other" fields to be aligned w/ "enumeration-value" fields
    // have to do this dynamically b/c these fields are
    // potentially hidden by tabs and/or accordions
    // this function gets called the 1st time a tab or accordion header is shown
    // (and only do this when both enumeration-value and enumeration-other are visible)
    // (they will be repositioned on the change event otherwise)
    $(parent).find(".enumeration-value").filter(":visible").each(function(index,value){
        var enumerationValue = $(this);        
        var enumerationOther = enumerationValue.siblings(".enumeration-other:first");
        $(enumerationOther).filter(":visible").offset({
            "left" : $(enumerationValue).offset().left
        });
    });    
};

/*
 * function to determine whether an add dialog box should appear upon pressing the add button
 * (if the addMode is INLINE only, then there is no point displaying the box)
 */
function add_step_zero(row) {
    add_button_type = $(row).closest("fieldset").find(".subform-toolbar > button.add").attr("class");
    if (add_button_type.indexOf("remote") != -1) {
        /* if the set of classes for the add button contains 'remote'... */
        add_step_one(row);
    }
    else {
        return true;
    }
}

/*
 * begin the adding process
 */
function add_step_one(row) {
    var url = window.document.location.protocol + "//" + window.document.location.host + "/metadata/add_form/";
    url += "?g=" + guid_to_add_to + "&a=" + app_to_add_to + "&m=" + model_to_add_to + "&f=" + field_to_add_to;

    
    $.ajax({
        url : url,
        type : 'get',
        success : function(data) {
            form_to_add = row;
            var content = "<div style='text-align: center; margin-left: auto; margin-right: auto;'>" + data + "</div>";
            $("#add-dialog").html(content);
        }
    });
    $("#add-dialog").dialog("open");
      // ideally, this fn would continue adding content.
      // but the dialog fn doesn't block,
      // so I'm doing this in two steps w/ a callback (add_step_two) on the "close" event of the dialog
      return true;
};

/*
 * finish the adding process
 */
function add_step_two() {
    var url = window.document.location.protocol + "//" + window.document.location.host + "/metadata/get_content/";
    url += "?g=" + guid_to_add_to + "&a=" + app_to_add_to + "&m=" + model_to_add_to + "&f=" + field_to_add_to + "&i=" + id_to_add


    $.ajax({
       url : url,
       type : 'get',
       success : function(data) {

           // populate the form w/ the newly-added data...
           populate($.parseJSON(data),form_to_add);
           // work out what the title of the form ought to be...
           var title = model_to_add + "&nbsp;<button type='button' class='remove' title='remove');'>remove</button>"
           $(form_to_add).find(".accordion-header a").html(title);
           // initialize the buttons in the titles for these forms...
           // (b/c they are being added after enableJQueryWidgets below)
           $(form_to_add).parents(".accordion:first").find(".accordion-header").each(function() {
              initializeRemoveButton($(this).find("a button.remove"));
           });            
       }
    });
    return true;
}

/* fn to setup properties of remove button */
/* this is handled outside of enableJQueryWidgets b/c it has to be run as new fields get added to the form */
function initializeRemoveButton(button) {

        $(button).button({
            icons: {primary: "ui-icon-circle-minus"},
            text: false
        });
        $(button).bind("click", function(e) {
            /* prevent the delete button from _actually_ opening the accordian tab */
            e.stopPropagation();
        });
        $(button).click(function(event) {


            var fieldset = $(event.target).closest("fieldset");
            var subform = $(event.target).closest(".subform");

            model_to_remove_from = $(fieldset).find("span.current_model_name:first").text();
            field_to_remove = $(fieldset).find("span.current_field_name:first").text();

            button_to_remove_form = $(subform).find(".delete-row");

            var content = "<div style='text-align: center; margin-left: auto; margin-right: auto;'>Do you really wish to remove this instance of " + field_to_remove + "?<p><em>(It will not be deleted, only removed from this " + model_to_remove_from + ")</em></p></div>";
            $("#remove-dialog").html(content);
            $("#remove-dialog").dialog("open");

            //$(button_to_remove_form).click();

        });
};

/* enable jquery widgets */
function enableJQueryWidgets() {
    $(function() {

       /* enable popup dialogs */
       $("#help-dialog").dialog({autoOpen:false,hide:'explode',modal:true});
       $("#add-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true,
            buttons : {
                ok : function() {
                    id_to_add = $(this).find("select").val();
                    model_to_add = $(this).find("select option:selected").text();
                    $(this).dialog("close");
                },
                cancel : function() {
                    id_to_add = ""
                    model_to_add = ""
                    $(this).dialog("close");
                }
            },
            close : function() {
                if (id_to_add != "") {
                    add_step_two();
                }
            }
        });
        $("#remove-dialog").dialog({
            autoOpen:false,hide:'explode',modal:true,
            buttons : {
                ok : function() {
                    $(this).dialog("close");
                },
                cancel : function() {
                    button_to_remove_form = "";
                     $(this).dialog("close");
                }
            },
            close : function() {
                if (button_to_remove_form != "") {
                    $(button_to_remove_form).click();
                }
            }
        });


       /* enable tabs */
       $(".tabs").tabs({
           show : function(event,ui) {               
               if ($(ui.tab).attr("class")!="dynamic-formset-initialized") {
                   $(ui.tab).addClass("dynamic-formset-initialized");
                   var tab_selector = $(ui.tab).attr("href");
                   $(tab_selector).find(".accordion").each(function() {
                       var prefix = $(this).attr("class").split(' ')[1];
                       /* the subform+prefix class is added after the multiopenaccordion method below */
                       /* (it's not in the actual template) */
                       var subform_selector = ".subform."+prefix;
                       $(subform_selector).formset({
                           prefix : prefix.split("-formset")[0],
                           added : function(row) {
                               // custom fn to call when user presses "add" for a particular row
                               add_step_zero(row);
                               //add_step_one(row);
                           },
                           // this _needs_ to be completely unique
                           formCssClass : "dynamic-"+prefix
                       });
                   });
               }
           }
       });
       $(".tabs ul li a").keydown(function(event) {
           var keyCode = event.keyCode || event.which;
           if (keyCode == 9) {
               currentTab = $(event.target);
               currentTabSet = $(currentTab).parents("div.tabs:first");
               /* make the tab key shift focus the the next tab */
               var nTabs = $(currentTabSet).tabs("length");
               var selected = $(currentTabSet).tabs("option","selected");
               /* (the modulus operator ensures the tabs wrap around) */
               $(currentTabSet).tabs("option","selected",(selected+1)%nTabs);               
           }
       });

       $('.tabs').bind('tabsshow', function(event, ui) {
           var tabPane = ui.panel;
           if ($(tabPane).attr("class").indexOf("resized-and-repositioned")==-1) {
               resizeFields(tabPane);
               repositionFields(tabPane);
               $(tabPane).addClass("resized-and-repositioned");
           }
       });

       /* explicitly resize & reposition the first tab
        * (since it won't fire the show event above
        */
       var currentTabPane = $(".tabs:first").find('.ui-tabs-panel:not(.ui-tabs-hide)');
       if ($(currentTabPane).attr("class").indexOf("resized-and-repositioned")==-1) {
           resizeFields(currentTabPane);
           repositionFields(currentTabPane);
           $(currentTabPane).addClass("resized-and-repositioned");
       }

       /* enable collapsible fieldsets */
       $(".coolfieldset").coolfieldset({speed:"fast"});

       /* enable multi-open accordions */
       $( ".accordion" ).multiOpenAccordion({
           active : "all",
           tabShown : function(event,ui) {
               var accordionHeader = ui['tab'];
               var accordionPane = ui['content'];              

               /* also need to customize fields in case they were hidden in a closed accordion up until now */
               if ($(accordionHeader).attr("class").indexOf("resized-and-repositioned")==-1) {
                   resizeFields(accordionPane);
                   repositionFields(accordionPane);
                   $(accordionHeader).addClass("resized-and-repositioned");
               }             
           }

       });
       


       /* have to do this in two steps b/c the accordion JQuery method above cannot handle any content inbetween accordion panes */
       /* but I need a container for dynamic formsets to be bound to */
       /* so _after_ multiopenaccordion() is called, I stick a div into each pane and bind the formset() method to it */
       $(".accordion").find(".accordion-header").each(function() {
           var prefix = $(this).closest(".accordion").attr("class").split(' ')[1];
           var div = "<div class='subform " + prefix + "'></div>";
           $(this).next().andSelf().wrapAll(div);
       });

       /* resize _some_ textinputs */
       // TODO: DOUBLE-CHECK THIS SELECTOR WORKS IN ALL CASES
       $('input[type=text].readonly').each(function(){
           // I could make this dynamic by using the keyup() function instead of each()
           // but, really, I only care about this for property names which are readOnly anyway
           var chars = $(this).val().length;
           $(this).attr("size",chars);
       });

       /* add functionality to help-buttons (icons masquerading as buttons) */
       $(".help-button").hover (
            function() {$(this).children(".ui-icon-info").addClass('hover-help-icon');},
            function() {$(this).children(".ui-icon-info").removeClass('hover-help-icon');}
       );
       $(".help-button").mouseover(function() {
            $(this).css('cursor', 'pointer');
       });
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

        /* enable enumeration widgets */
        /* (these are multiwidgets: a choice and a textfield) */
        /* (the latter is only shown when the former is set to "OTHER") */
        $(".enumeration-value").each(function() {
            enumerationValue = $(this);
            //enumerationOther = enumerationValue.next(".enumeration-other");
            enumerationOther = enumerationValue.siblings(".enumeration-other:first");

            if (enumerationValue.attr("multiple")=="multiple") {
                multipleValues = enumerationValue.val();
                // TODO: CHECK THE INDEXOF FN IN IE                
                if (! multipleValues || multipleValues.indexOf("OTHER")==-1) {
                    enumerationOther.hide();
                }
                else {
                    enumerationOther.show();
                }
                
                /* if NONE is selected, then all other choices should be de-selected */
                if ( multipleValues && multipleValues.indexOf("NONE") != -1) {
                    enumerationValue.val("NONE")
                    enumerationOther.hide();
                }
            }
            else {
                if (enumerationValue.val()=="OTHER") {
                    enumerationOther.show();
                    
                    $(enumerationOther).offset({
                        "left" : $(enumerationValue).offset().left
                    });

                }
                else {
                    enumerationOther.hide();
                }
            }
            
            // position the "other" textbox relative to the "value" select
            enumerationOther.before("<br/>");
            // THIS HAS BEEN MOVED TO THE REPOSITIONFIELDS FN
            // WHICH GETS CALLED WHEN TABS & ACCORDIONS ARE FIRST SHOWN
            // THERE'S NO NEED TO CALL IT HERE'
//            $(enumerationOther).offset({
//                "left" : $(enumerationValue).offset().left
//            });

        });        
        $(".enumeration-value").change(function(event) {
            enumerationValue = $(event.target);
            //enumerationOther = enumerationValue.next(".enumeration-other");
            enumerationOther = enumerationValue.siblings(".enumeration-other:first");
            if (enumerationValue.attr("multiple")=="multiple") {
                multipleValues = enumerationValue.val();
                // TODO: CHECK THE INDEXOF FN IN IE
                //if (! multipleValues || multipleValues.indexOf("OTHER")==-1) {
                if (multipleValues.indexOf("OTHER")==-1) {
                    enumerationOther.hide();
                }
                else {
                    enumerationOther.show();
                }
                
                /* if NONE is selected, then all other choices should be de-selected */
                if ( multipleValues && multipleValues.indexOf("NONE") != -1) {
                    enumerationValue.val("NONE")
                    enumerationOther.hide();
                }


            }
            else {
                if (enumerationValue.val()=="OTHER") {
                    enumerationOther.show();
                }
                else {
                    enumerationOther.hide();
                }
            }
            
            // HOWEVER, I USE THE SAME LOGIC HERE
            // B/C THE ENUMERATIONS IN QUESTION MAY NOT HAVE BEEN VISIBLE
            // WHEN REPOSITION FIELDS WAS ORIGINALLY CALLED
            $(enumerationOther).filter(":visible").offset({
                "left" : $(enumerationValue).offset().left
            });
        });
        

        /* custom code to disable a widget (used when field is customized to 'readonly') */
        /* turns out that disabling it directly in Django causes the value to be set to None,
         * which means, the incorrect value is saved */
        $(".disabled").each(function() {            
            $(this).attr('disabled','true');

        });

        /* init an 'enabler' - a field that controls other fields or forms */
        $(".enabler:not(.enumeration-other)").each(function() {
            // the onchange method is bound to the toggleStuff function
            $(this).trigger("change");
        });

        /* enable calendar widgets */
        $(".datepicker").datepicker(
            {changeYear : true, showButtonPanel : true, showOn : 'button', buttonImage : '/static/django_cim_forms/img/calendar.gif'}
        );
        $(".ui-datepicker-trigger").mouseover(function() {
            $(this).css('cursor', 'pointer');
        });
        $(".ui-datepicker-trigger").attr("title","click to select date");
        $(".ui-datepicker-trigger").css("vertical-align","middle");

        /* enable _fancy_ buttons */
        $(".button").button();
        $(".subform-toolbar button").mouseover(function() {
            $(this).css('cursor', 'pointer');
        });
        $(".subform-toolbar button.expand" ).button({
             icons : {primary: "ui-icon-circle-triangle-s"},
             text : false
        }).click(function(event) {
            var formset = $(event.target).closest("fieldset");
            var accordion = $(formset).find(".accordion:first");
            // I have to do this manually (rather than w/ the active:all option)
            // b/c the content between accordions messes things up
            $(accordion).find(".accordion-content").show();
        });
        $(".subform-toolbar button.collapse" ).button({
            icons : {primary: "ui-icon-circle-triangle-n"},
            text: false
        }).click(function(event) {
            var formset = $(event.target).closest("fieldset");
            var accordion = $(formset).find(".accordion:first");
            // I have to do this manually (rather than w/ the active:none option)
            // b/c the content between accordions messes things up
            $(accordion).find(".accordion-content").hide();
        });

        $("button.remove").each(function(){
            // doing this in a separate fn b/c these buttons are created and destroyed dynamically
            // so I need to re-initialize new ones as they appear
            initializeRemoveButton($(this));
        });
        
        $(".subform-toolbar button.add").button({
            icons: {primary: "ui-icon-circle-plus"},
            text: false
        }).click(function(event) {
            
            fieldset = $(event.target).closest("fieldset");

            // there are two situations where I can be adding/replacing content
            // either a subForm or a subFormSet
            if ($(event.target).hasClass("FORM")) {
                form_to_add = $(fieldset);

            }
            else {
                // form_to_add is set in add_step_one
            }

            guid_to_add_to = $(fieldset).find("span.current_guid:first").text();
            model_to_add_to = $(fieldset).find("span.current_model:first").text();
            app_to_add_to = $(fieldset).find("span.current_app:first").text();
            field_to_add_to = $(fieldset).find("span.current_field:first").text();

            var add_button = $(fieldset).find(".add-row:first");
            $(add_button).click();

        });
    });

};
