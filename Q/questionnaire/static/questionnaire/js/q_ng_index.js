/* q_ng_index.js */
/* ng app for dealing w/ QProjects in the q_index.html template */

(function() {
    var app = angular.module("q_index", ["q_base"]);

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

    app.controller("IndexController", ['$http', function($http) {

        /* this is a _very_ minimal ng Controller app */
        /* in fact, it probably doesn't even need to inherit from "q_base" above */
        /* but it keeps the codebase similar for all of my custom page apps */

        var index_controller = this;
        index_controller.projects = []; // initial data

        $http.get("/api/projects/?is_active=true&is_displayed=true&ordering=order", {format: "json"})
            .success(function(data) {
                index_controller.projects = data.results;

            })
            .error(function(data) {
                console.log(data);
            });

    }]);

    /***********/
    /* THE END */
    /***********/

})();