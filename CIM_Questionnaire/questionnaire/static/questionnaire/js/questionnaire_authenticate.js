/* functions specific to the login/logout */

function projects(parent) {
    $(parent).find("select[name='projects'].multiselect").multiselect({
        autoOpen    : true,
        header      : false,
        height      : 'auto',
        beforeclose : function(event,ui) {
            return false;
        }
    });
}

function providers(parent) {
    $(parent).find(".provider_choice").each(function() {
            $(this).parents("ul:first").addClass("provider_choices");
        });

        /* initialize provider choices (one-off for this page only) */
        /* NO LONGER USING THIS CUMBERSOME CODE; JUST CHANGING WIDGET DIRECTLY IN VIEW
        $(".provider_choices").each(function(i,e) {
            var provider = e;
            var name = $(provider).attr("name");
            $(e).find("option").each(function(i,e) {
                var option  = e;
                var id      = name + "_" + $(option).val();
                var img_src = {{ MEDIA_URL }} + PROVIDER_IMAGES[$(option).val()];
                var radio_input = $(
                    "<div class='provider_choice'>" +
                        "<input type='radio' id='" + id + "' name='" + name + "'/>" +
                        "<label for='" + id + "'>" +
                            "<img align='center' title='" + $(option).text() + "' height='32px' src='" + img_src + "'/>" +
                        "</label>" +
                    "</div>");
                $(radio_input).click(function() {
                    $(option).attr("selected","selected");
                });
                $(provider).after(radio_input);
            });
        });
        */
}