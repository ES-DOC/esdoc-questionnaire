/* q_model.js */
/* angular app for dealing w/ QProjects in the index */

(function() {

    /* this is a _very_ minimal ng app */
    /* in fact, it probably doesn't even need to inherit from "q_base" below */
    /* but it keeps the codebase similar for all of my custom page apps */

    var app = angular.module("q_index", ["q_base"]);

    app.controller("IndexController", [ "$http", "$log", function($http, $log) {

        var index_controller = this;
        index_controller.projects = []; // initial data
        $http.get("/api/projects/?is_active=true&is_displayed=true&ordering=title", {format: "json"})
            .success(function(data) {
                index_controller.projects = data.results;
            })
            .error(function(data) {
                console.log(data);
            });

    }]);


})();

