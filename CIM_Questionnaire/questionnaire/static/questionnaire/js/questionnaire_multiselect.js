/* custom JQuery widget plugin */

/* adds checkboxes or radiobuttons to selects
 * (existing jquery plugins all did this via dialogs outside of the DOM,
 * which screwed up my placement options, so I've written my own)
 *
 */
$.widget("questionnaire.multiselect", {

    // default options
    options: {
        autoOpen        : false,
        multiple        : true,
        sortable        : false,
        numToShow       : 1,
    	emptySingleText : 'Select option',
        emptyMultiText  : 'Select options',
        onChange        : null
    },

    _setOption : function( key, value ) {
        this.options[ key ] = value;
        this._update(key);
    },

    _update : function(key) {
        var options = this.options;
        var element = this.element;
        var widget  = $(element).next();
        var header  = $(widget).find(".multiselect_header");
        var content = $(widget).find(".multiselect_content");
        
        if (key=='autoOpen') {
            if (options.autoOpen) {
                $(content).show();
            }
            else {
                $(content).hide();
            }
        }
        else if (key=='multiple') {
            console.log("TODO: update for 'multiple' option");
        }
        else if (key=='sortable') {
            if (options.sortable) {
                this._sortable();
            }
            else {
                console.log("TODO: update for 'sortable=false' option");
            }
        }
        else if (key=='numToShow') {
            this._set_text();
        }
        else if (key=='emptySingleText') {
            this._set_text();
        }
        else if (key=='emptyMultiText') {
            this._set_text();
        }
        else if (key=='onChange') {
            
        }
        else {
            console.log("invalid option: " + key)
        }
    },

    _sortable : function() {

        var element = this.element;
        var options = this.options;
        var widget  = $(element).next();
        var header  = $(widget).find(".multiselect_header");
        var content = $(widget).find(".multiselect_content");

            $(content).find("label").each(function() {
                var sortable_icon = $("<span style='float: right;' class='ui-icon ui-icon-arrow-2-n-s' title='drag and drop to reorder'/>");
                $(this).append(sortable_icon);
            });

            $(content).sortable({
                axis        : "y",
                placeholder : "sortable_item",
                start : function(e, ui){
                    ui.placeholder.height(ui.item.height());
                    ui.placeholder.width("400");
                },
                stop : function(e,ui) {
                    var sorted_item = ui["item"];
                    $(sorted_item).addClass("sorting")

                    var ordered_value_list = $(content).find("label").map(function() {
                        return $(this).find("input").attr("value");
                    }).get();
                    var element_options = $(element).children("option").get();
                    element_options.sort(function(a,b) {
                        a_order = ordered_value_list.indexOf($(a).attr("value"));
                        b_order = ordered_value_list.indexOf($(b).attr("value"));
                        return a_order > b_order;
                    });
                    $.each(element_options, function(option_index, element_option) {
                        element.append(element_option);
                    });
                }
            });
    },

    _set_text : function() {
        var options = this.options;
        var element = this.element;
        var widget  = $(element).next();
        var header  = $(widget).find(".multiselect_header");
        var content = $(widget).find(".multiselect_content");

        if (options.multiple) {
            var selected_choices = $(element).find("option:selected").map(function() {
                return "\"" + $(this).text() + "\"";
            }).get();
            var num_selected_choices = selected_choices.length;
            if (num_selected_choices == 0) {
                var new_label = options.emptyMultiText;
            }
            else if (num_selected_choices <= options.numToShow) {
                var new_label = selected_choices.join(", ")
            }
            else {
                var new_label = selected_choices.slice(0,options.numToShow).join(", ") + " + " + (num_selected_choices-options.numToShow) + " more"
            }
        }
        else {
            var selected_choice = $(element).find("option:selected");
            // a val of "" is the EMPTY_CHOICE
            if (selected_choice.length && $(selected_choice).val() != "") {
                var new_label = "\"" + $(selected_choice).text() + "\""
            }
            else {
                var new_label = options.emptySingleText;
            }
            
        }
        $(header).button("option","label",new_label);
        $(header).trigger("change"); // this provides a hook for other js methods
    },

    _create : function(){
        var multiselect = this;

        var element = this.element;
        var options = this.options;

        var element_id   = $(element).attr("id");
        var element_name = $(element).attr("name")

        if (options.multiple) {
            var widget  = $("<div class='ui-multiselect ui-widget ui-corner-all multiple'></div>");
        }
        else {
            var widget  = $("<div class='ui-multiselect ui-widget ui-corner-all single'></div>");
        }
        var header  = $("<button class='multiselect_header' type='button'><span class='multiselect_header_title'>&nbsp;</span></button>");
        var content = $("<div class='multiselect_content ui-widget ui-widget-content ui-corner-all'></div>");

        // setup header
        $(header).button({
            icons : {
              primary : options.autoOpen ? "ui-icon-triangle-1-e" : "ui-icon-triangle-1-s"
            },
            label : options.multiple ? options.emptyMultiText : options.emptySingleText,
            text : true
        }).click(function() {
           $(content).toggle();
           var icon = $(this).find(".ui-icon:first");
           $(icon).toggleClass("ui-icon-triangle-1-s ui-icon-triangle-1-e");
        });

        $(header).show(function(){
            // force the text to be rendered even if the widget was hidden to start
            multiselect._set_text();
        });

        // setup content
        $(element).find("option").each(function() {
            var element_choice  = $(this);
            var value   = $(element_choice).attr("value");
            var text    = $(element_choice).text();
            var id      = element_id + "-" + value;

            if (options.multiple) {
                var type = "checkbox";
            }
            else {
                var type = "radio";
            }
            var widget_choice   = $("<label previous_value='unchecked' style='display: block;' for='"+id+"'><input id='"+id+"' name='"+element_name+"-multiselect' type='"+type+"' value='"+value+"'>&nbsp;"+text+"</input></label>")
          
            $(widget_choice).click(function(event) {
                // this bit of code prevents responding to click events if they were triggered during sorting
                if ($(this).hasClass("sorting")) {
                    $(this).removeClass("sorting");
                    $(element).trigger("change");
                    event.stopPropagation();
                    return false;
                    /*
                    if ($(this).hasClass("selected")) {
                        $(this).find("input").prop("checked",false);
                    }
                    else {
                        $(this).find("input").prop("checked",true);
                    }
                    */
                }

                // this clever bit of code allows you to uncheck a single option
                if (! options.multiple) {
                    if ($(this).hasClass("selected")) {
                        $(this).find("input").prop("checked",false);
                        $(this).trigger("change");
                    }
                }                
                
            });

            $(widget_choice).change(function(event) {

                if (options.multiple) {
                    $(this).toggleClass("selected");
                }
                else {
                    $(element).find("option").prop("selected",false);
                    if ($(this).hasClass("selected")) {
                        $(content).find("label").removeClass("selected");
                    }
                    else {
                        $(content).find("label").removeClass("selected");
                        $(this).addClass("selected");
                    }
                }

                if ($(this).hasClass("selected")) {
                    $(element_choice).prop("selected",true);
                }
                else {
                    $(element_choice).prop("selected",false);
                }

                multiselect._set_text();
                multiselect._trigger("onChange", null, { choice : $(element_choice) } );
                $(element_choice).change();
            });

            if (value) {
                if ($(element_choice).is(":selected")) {
                    $(widget_choice).find("input").prop("checked",true);
                    $(widget_choice).trigger("change");
                }
                $(content).append(widget_choice);
            }
        });

      

        // put it all together
        if (! options.autoOpen) {
            $(content).hide();
        }
        $(widget).append(header);
        $(widget).append(content);
        $(widget).insertAfter(element);
        $(element).hide();

        // and some fine-tuning...
        if (options.sortable) {
            this._sortable();
        }

    }

});
