/* q_ng_customizer.js */
/* ng app for dealing w/ User Profiles */

(function() {
    var app = angular.module("q_user", ["q_base", "ngCookies", "ui.bootstrap", "ui.sortable", "ng.django.forms"]);

    app.config(['$httpProvider', function($httpProvider) {
        /* TODO: MOVE THIS AJAX LOGIC INTO q_base */
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    }]);

    app.controller("UserController", [ "$scope", "$http", "$cookies", function($scope, $http, $cookies) {

        /* do stuff here */

    }]);

})();




