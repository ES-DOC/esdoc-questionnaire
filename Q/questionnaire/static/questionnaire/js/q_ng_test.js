/* q_ng_editor.js */
/* ng app for dealing w/ QRealizations */

(function() {
    var app = angular.module("q_test", ["q_base", "ui.bootstrap", "ng.django.forms"]);

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

        $scope.add_node = function() {
            var new_node = {
                "name": "new node",
                "documentation": "documentation for one.one.one",
                "key": "one.one.one",
                "path": "_DATA",
                "is_selected": False,
                "is_active": True,
                "is_complete": False,
                "nodes": []
            };
            $scope.hierarchy["nodes"].push(new_node);
            console.log("foo");
        };

    }]);

    app.controller("ModelEditorController", ['$scope', '$global_services', '$attrs', '$http', '$location', '$filter', function($scope, $global_services, $attrs, $http, $location, $filter) {

        /* clear any parent scope */
        /* (as per http://stackoverflow.com/a/23225510/1060339) */
        /* Angular always checks parent scope to see if there is a variable w/ the same name ("prototypical inheritance") */
        /* b/c of the highly recursive nature of the Q, there will almost always be parent scope variables w/ the same name */
        /* but I want to keep these all separate (among other things, it lets me simplify forms' "scope_prefix" in "forms_edit_properties.QPropertyRealizationFormSet#add_default_form_arguments")
        /* hooray!!! */
        $scope.current_model = {};

        /* TODO: DO I NEED TO ADD THE ABOVE LINE TO SIMILAR PLACES IN "q_ng_customizer.js" ? */
        /* TODO: Angular docs recommend something a bit more complex: https://docs.angularjs.org/guide/directive#isolating-the-scope-of-a-directive */

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(
            function () {
                return $global_services.isLoaded();
            },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    $scope.current_model_path = $attrs.currentModelPath;
                    $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                    /* HARD-CODING THIS; UNLIKE CUSTOMIZATIONS I WANT TO DISPLAY EVERYTHING (LOAD THE FORM) UPON CONTROLLER LOAD */
                    $scope.current_model.display_detail = true;
                    $scope.is_loaded = true;
                }
            }
        );

        $scope.update_model_completion = function() {
            /* computes a model's completion based on its properties' completion */
            var properties_completion = $scope.current_model['properties'].reduce(function(value, property) {
                /* using 'reduce' above instead of 'map' in order to exclude meta properties */
                if (! property.is_meta) {
                    value.push(property.is_complete)
                }
                return value;
            }, [])
            $scope.current_model['is_complete'] = properties_completion.every(function(is_complete) {
                return is_complete;
            });
        };

    }]);

    /***********/
    /* THE END */
    /***********/

})();