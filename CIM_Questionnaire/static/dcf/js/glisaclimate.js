_DATA = {}
function render_table(url) {
         $.ajax({ 
             url : url,
//             type : "GET",
//             dataType : "json",
//dataType: "html",
             statusCode: {
                404: function() {
                  $("#response").html('Could not contact server.');
                },
                500: function() {
                  $("#response").html('A server-side error has occurred.');
                }
             },
             error : function(jqXHR,textStatus,errorThrown) {
               $("#response").html("an error has occured");
	    },
             success : function(data) {
                 alert($(data).find(".view-content").attr("class"));
             },
             complete : function() {

             },

         })

};
