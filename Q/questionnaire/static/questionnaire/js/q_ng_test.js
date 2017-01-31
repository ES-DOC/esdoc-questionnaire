/* q_ng_editor.js */
/* ng app for dealing w/ QRealizations */

(function() {
    var app = angular.module("q_editor", ["q_base", "ui.bootstrap", "ng.django.forms"]);

    /**********/
    /* CONFIG */
    /**********/

    app.config(['$httpProvider', '$provide', function($httpProvider, $provide) {

        /* TODO: MOVE THIS AJAX LOGIC INTO q_base */
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    }]);

    /*************/
    /* FACTORIES */
    /*************/

    /***************/
    /* CONTROLLERS */
    /***************/

    /************************/
    /* top level controller */
    /************************/

    app.controller("EditorController", ['$scope', '$global_services', '$attrs', '$http', '$location', '$filter', function($scope, $global_services, $attrs, $http, $location, $filter) {

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        /* TODO: DELETE THIS ONCE EVERYTHING WORKS */
        $scope.print_stuff = function() {
            /* print the current state of stuff */
            console.log("session_key=" + session_key);
            console.log($global_services.getModelFromPath("_DATA"));
            console.log($scope.hierarchy);
        };

        $scope.hierarchy = {};

        $global_services.load("/services/test");

        $scope.is_loaded = false;
        $scope.$watch(
            function () {
                return $global_services.isLoaded();
            },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    $scope.load();
                    $scope.is_loaded = true;
                }
            }
        );

        $scope.load = function() {
            $global_services.setBlocking(true);
            var url = "/services/get_hierarchy/";
            $http({
                method: "GET",
                url: url,
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            })
            .then(
                function(result) {
                    /* success */
                    $scope.hierarchy = result.data;
                    $global_services.setBlocking(false);
                },
                function(error) {
                    /* error */
                    console.log(error.data);
                    $global_services.setBlocking(false);
                }
           )
        };

    }]);


    /***********/
    /* THE END */
    /***********/

})();