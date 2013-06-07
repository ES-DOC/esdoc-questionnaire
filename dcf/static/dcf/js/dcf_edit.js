// THIS ADDS ONTO THE FUNCTIONALITY IN dcf_customize.js
// I REALLY OUGHT TO REFACTOR ALL OF THIS OUT INTO SENSIBLE FILES


/* main fn */
var EDIT = {
    enableDCF : function() {

        $("button.add").button({
            icons: { primary : "ui-icon-circle-plus" },
            text: true
        }).click(function(event) {
            alert("you clicked add!");
        });

        $("button.remove").button({
            icons: { primary : "ui-icon-circle-minus" },
            text: true
        }).click(function(event) {
            alert("you clicked remove!");
        });


    }

    /* end enableDCF fn */
};

