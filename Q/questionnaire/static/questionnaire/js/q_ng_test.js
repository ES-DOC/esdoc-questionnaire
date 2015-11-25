/* q_customizer.js */
/* angular app for dealing w/ QCustomizations */

(function() {
    var app = angular.module('q_test', ["q_base", "ngCookies", "ui.bootstrap", "ng.django.forms"]);

    app.config(['$httpProvider', function($httpProvider) {
        /* TODO: MOVE THIS AJAX LOGIC INTO q_base */
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    }]);

    app.controller('TestController', ["$scope", "$http", "$cookies", function($scope, $http, $cookies) {

        /* set initial data */
        $scope.api_url = api_url_dirname + api_url_basename;
        $scope.model_customization = {};
        $scope.server_errors = {};

        /* (re)load data */
        $scope.load = function() {

            if (api_url_basename) {

                $http.get($scope.api_url, {format: "json"})
                    .success(function (data) {
                        $scope.model_customization = data;
                    })
                    .error(function (data) {
                        console.log(data);
                    });

            }
        };

        $scope.foobar = function () {

            alert('hello');
        };

        $scope.load();

    }]);


})();




