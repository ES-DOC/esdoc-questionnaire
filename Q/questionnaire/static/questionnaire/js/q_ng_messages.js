/* ng_messages.js */
/* angular app for dealing w/ Django messages */

/************************************************************/
/* THIS IS NO LONGER BEING USED!                            */
/* B/C GETTING MULTIPLE NG APPS TO PLAY TOGETHER WAS HARD!  */
/* INSTEAD, I USE JQUERY (see "check_msg()" in "q_base.js") */
/************************************************************/

//(function() {
//    var app = angular.module("messages", ["ngCookies"]);
//
//    app.config(['$httpProvider', function($httpProvider) {
//
//        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
//        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
//        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
//
//    }]);
//
//    app.controller("MessagesController", [ "$http", function($http) {
//
//        var messages_controller = this;
//
//        messages_controller.messages = [];  // initial data
//
//        this.load = function() {
//            $http.get("/services/messages/")
//                .success(function (data) {
//                    messages_controller.messages = data;
//
//                    $.each(messages_controller.messages, function (i, message) {
//                        var box = bootbox.alert(message.text);
//                        box.find(".modal-content").addClass(message.status);
//                    })
//                })
//
//                .error(function (data) {
//                    console.log(data);
//                });
//        };
//
//        messages_controller.load();
//
//    }]);
//
//})();

