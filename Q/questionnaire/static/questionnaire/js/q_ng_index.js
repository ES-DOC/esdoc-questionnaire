/* q_model.js */
/* angular app for dealing w/ QProjects in the index */

(function() {
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

