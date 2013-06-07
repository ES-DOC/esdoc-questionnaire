/* top-level dcf JS code */

/* TODO: EVENTUALLY, I'LL MOVE TO SOMETHING LIKE BACKBONE TO RE-ORGANIZE MY JS  */
/* IN THE MEANTIME, I HAVE SEPARATED THEM OUT INTO MULTIPLE FILES,              */
/* AND INCLUDED RELEVANT FNS FROM EACH ONE IN A VAR (LIKE NAMESPACING)          */
/* THIS ISN'T PERFECT, BUT IT MAKES LIFE A BIT EASIER                           */

function loadJS(js_path) {
    // this fn loads another script
    // I am not useing the getScript() fn, b/c that does not cache results
    // instead I just make a standard AJAX call, but set "cache" to "true"
    options = {dataType : "script", cache : true, url : js_path}
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

        /* combo-boxes w/ checkboxes/radioboxes */
        $(".dropdownchecklist").multiselect({
            autoOpen : false,
            minWidth : 500,
            position : {
                my: "left bottom",
                at: "left top"
            },
            create : function(event, ui) {
                var values = $(event.target).multiselect("getChecked").map(function(){
                    return this.value;
                }).get();

                var enumeration_value = $(event.target)
                var enumeration_other = $(enumeration_value).siblings(".enumeration-other:first");

                if (values.indexOf("OTHER") != -1) {
                    // if "--OTHER--" is selected, then show the enumeration-other
                    $(enumeration_other).width($(enumeration_value).siblings(".ui-multiselect:first").width());
                    $(enumeration_other).show();
                }
                else {
                    $(enumeration_other).hide();
                }
                if (values.indexOf("NONE") != -1) {
                    // if "--NONE--" is selected, then de-select everything else
                    $(event.target).multiselect("getChecked").each(function() {
                        if (this.value != "NONE") {
                            this.click();
                        }
                    });
                    $(enumeration_other).hide(); // (including the other textbox)
                }

                // sometimes these lists have an onchange event
                // force the event callback to run upon initialization
                $(this).trigger("change");
            },
            close : function(event,ui) {
                var values = $(event.target).multiselect("getChecked").map(function(){
                    return this.value;
                }).get();

                var enumeration_value = $(event.target)
                var enumeration_other = $(enumeration_value).siblings(".enumeration-other:first");

                if (values.indexOf("OTHER") != -1) {
                    // if "--OTHER--" is selected, then show the enumeration-other
                    $(enumeration_other).width($(enumeration_value).siblings(".ui-multiselect:first").width());
                    $(enumeration_other).show();
                }
                else {
                    $(enumeration_other).hide();
                }
                if (values.indexOf("NONE") != -1) {
                    // if "--NONE--" is selected, then de-select everything else
                    $(event.target).multiselect("getChecked").each(function() {
                        if (this.value != "NONE") {
                            this.click();
                        }
                    });
                    $(enumeration_other).hide(); // (including the other textbox)
                }
            }
        });
        $(".dropdownchecklist[multiple]").multiselect({
            noneSelectedText : "please enter selections",
            selectedText : function(numChecked, numTotal, checkedItems){
                if ($("#customize").length) {
                    return numChecked + ' of ' + numTotal + ' selected';
                }
                MAX_LENGTH = 40;
                if (numChecked > 0) {
                    text = "\"" + checkedItems[0].value.substr(0,MAX_LENGTH);
                    if (checkedItems[0].length >= MAX_LENGTH) {
                        text += "...\"";
                    }
                    else {
                        text += "\"";
                    }                    
                    if (numChecked > 1) {
                        text += "  + " + (numChecked-1) + " more selections"
                    }
                    return text
                }
            },
            header : true           
        });
        $(".dropdownchecklist:not([multiple])").multiselect({
            noneSelectedText : "please enter selection",
            selectedList : 1,
            multiple : false,
            header : false,
            /* these next two handlers extend the plugin so that
             * de-selecting an option in single mode causes the noneSelectedText to be shown */
            open : function(event,ui) {
                $(event.target).attr("previous_selection",$(event.target).val());
            },
            click : function(event,ui) {
                if ($(event.target).attr("previous_selection") == ui.value)  {
                    $(event.target).multiselect("uncheckAll");
                }
            }
        });

        $(".enumeration-other").each(function() {
            $(this).css("font-style","italic");
            $(this).before("<br/>");
        });
        $(".enumeration-other").change(function() {
            var default_text = "please enter custom selection (or else deselect '--OTHER--' above)";
            var value = $(this).val().replace(/\s+/g,'');
            if (value) {
                $(this).css("font-style","normal");
            }
            else {
                $(this).val(default_text);
                $(this).css("font-style","italic");
            }
        });

        /* enable calendar widgets */
        $(".datepicker").datepicker({
            changeYear : true,
            showButtonPanel : false,
            showOn : 'button'
        }).next("button").button({
            icons : {
                primary : "ui-icon-calendar"
            },
            text : false
        });
        $(".ui-datepicker-trigger").mouseover(function() {
            $(this).css('cursor', 'pointer');
        });
        $(".ui-datepicker-trigger").attr("title","click to select date");
        //$(".ui-datepicker-trigger").css("vertical-align","middle");

        /********************************************/
        /* now call the enablers for other js files */
        /********************************************/
        CUSTOMIZE.enableDCF();
        EDIT.enableDCF();
                
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
            minWidth : 500,
            position : {
                my: "left bottom",
                at: "left top"
            },
            create : function(event, ui) {
                var values = $(event.target).multiselect("getChecked").map(function(){
                    return this.value;
                }).get();                

                var enumeration_value = $(event.target)
                var enumeration_other = $(enumeration_value).siblings(".enumeration-other:first");

                if (values.indexOf("OTHER") != -1) {
                    // if "--OTHER--" is selected, then show the enumeration-other
                    $(enumeration_other).width($(enumeration_value).siblings(".ui-multiselect:first").width());
                    $(enumeration_other).show();
                }
                else {
                    $(enumeration_other).hide();
                }
                if (values.indexOf("NONE") != -1) {
                    // if "--NONE--" is selected, then de-select everything else
                    $(event.target).multiselect("getChecked").each(function() {
                        if (this.value != "NONE") {
                            this.click();
                        }
                    });
                    $(enumeration_other).hide(); // (including the other textbox)
                }

                // sometimes these lists have an onchange event
                // force the event callback to run upon initialization
                $(this).trigger("change");
            },
            close : function(event,ui) {
                var values = $(event.target).multiselect("getChecked").map(function(){
                    return this.value;
                }).get();

                var enumeration_value = $(event.target)
                var enumeration_other = $(enumeration_value).siblings(".enumeration-other:first");

                if (values.indexOf("OTHER") != -1) {
                    // if "--OTHER--" is selected, then show the enumeration-other
                    $(enumeration_other).width($(enumeration_value).siblings(".ui-multiselect:first").width());
                    $(enumeration_other).show();
                }
                else {
                    $(enumeration_other).hide();
                }
                if (values.indexOf("NONE") != -1) {
                    // if "--NONE--" is selected, then de-select everything else
                    $(event.target).multiselect("getChecked").each(function() {
                        if (this.value != "NONE") {
                            this.click();
                        }
                    });
                    $(enumeration_other).hide(); // (including the other textbox)
                }
            }
        });
        $(parent).find(".dropdownchecklist[multiple]").multiselect({
            noneSelectedText : "please enter selections",
            selectedText : function(numChecked, numTotal, checkedItems){
                if ($("#customize").length) {
                    return numChecked + ' of ' + numTotal + ' selected';
                }
                MAX_LENGTH = 40;
                if (numChecked > 0) {
                    text = "\"" + checkedItems[0].value.substr(0,MAX_LENGTH);
                    if (checkedItems[0].length >= MAX_LENGTH) {
                        text += "...\"";
                    }
                    else {
                        text += "\"";
                    }
                    if (numChecked > 1) {
                        text += "  + " + (numChecked-1) + " more selections"
                    }
                    return text
                }
            },
            header : true
        });
        $(parent).find(".dropdownchecklist:not([multiple])").multiselect({        
            noneSelectedText : "please enter selection",
            selectedList : 1,
            multiple : false,
            header : false,
            /* these next two handlers extend the plugin so that
             * de-selecting an option in single mode causes the noneSelectedText to be shown */
            open : function(event,ui) {
                $(event.target).attr("previous_selection",$(event.target).val());
            },
            click : function(event,ui) {
                if ($(event.target).attr("previous_selection") == ui.value)  {
                    $(event.target).multiselect("uncheckAll");
                }
            }
        });


        $(parent).find(".enumeration-other").each(function() {
            $(this).css("font-style","italic");
            $(this).before("<br/>");
        });
        $(parent).find(".enumeration-other").change(function() {
            value = $(this).val().replace(/\s+/g,'');
            if (value) {
                $(this).css("font-style","normal");
            }
            else {
                $(this).val("please enter custom selection");
                $(this).css("font-style","italic");
            }
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
           if ($(target).length>1) {
               // yep, it's a multiwidget...
               for (var i=0; i<targetValue.length; i++) {
                   // so it must have been passed an array of values,
                   // map each value to the corresponding multiwidget widget (unless the value is an explicit 'none')
                   if (targetValue[i]!="None") {
                       $(target[i]).val(targetValue[i]);
                   }
               }

           }
           else {
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
   }
};



/* restricts the set of options of a set of target fields
 * to the selected options of the source field
 * (targets must be in the same form/subform)
 */
function restrict_options(source,targets) {
    var restrictions = [];
    $(source).find("option:selected").each(function() {
        restrictions.push($(this).val());
    });

    for (var i=0; i<targets.length; i++) {
        var selector = "*[name='" + targets[i] + "']";
        var target = $(source).closest(".form").find(selector).find("select");
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
            $(target).find("option[value='"+this+"']").remove();
        });
        // add everything in restrictions and not in options
        $(in_restrictions_but_not_options).each(function() {
            var option = $(source).find("option[value='"+this+"']");
            $(target).append($("<option>").attr("value",this).text($(option).text()));

        });

        // refresh the multiselect widget if needed
        if ($(target).hasClass("dropdownchecklist")) {
            $(target).multiselect("refresh");
        };

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
        var new_text = ($(item).val()) ? $(item).find("option:selected").text() : "None";
        if (new_text=="") {
            new_text = "None";
        }
        $(label).text( new_text );
    }
    else if (input_type=="input") {
        var new_text = ($(item).val()) ? $(item).val() : "None";
        $(label).text( new_text );
    }
    
    //var new_text = ($(item).val()) ? $(item).find("option:selected").text() : "None";
    //$(label).text( new_text );
};



/* copies (JSON) data - in most cases the global categories dictionaries - to a field
 * - in most cases the otherwise unused "attribute_categories_content" or "property_categories-content"
 * this makes sure that any edits to the tags gets saved in the view
 */
function copy_data_to_field(dataName,fieldName) {
    var data = window[dataName];
    var field = $("form input[name='"+fieldName+"']")
    $(field).val(JSON.stringify(data));
};

/* display an error in the correct location
 * also, color any containing tabs or accordions */
function render_error(error) {
    // render accordions
    $(error).parents(".accordion-content").each(function() {
        $(this).prev(".accordion-header").addClass("ui-state-error");
    });
    // render tabs
    $(error).parents(".tab_content").each(function() {
        var tab_id = $(this).closest(".ui-tabs-panel").attr("id");
        $("a[href='#"+tab_id+"']").closest("li").addClass("ui-state-error");
    });
    // render fieldsets
    $(error).parents(".coolfieldset").each(function() {
        // (doing this manually instead of via JQuery's built-in UI system)
        // (b/c it would indicate that everything in the fieldset is in error)'    
        $(this).addClass("error");
    });
};

function render_msg(parent) {
   /* if a msg exists, then display it */
    var msg = $(parent).find("#msg").text().trim();
    if (msg && msg.length) {
        $(parent).find("#msg").dialog({
            modal : true,
            hide : "explode",
            height : 150,
            width : 350,
            title: "<span class='ui-icon ui-icon-notice'></span>",
            buttons: {
                OK: function() {
                    $(this).dialog("close");
                }
            }
        });
    }
};
     