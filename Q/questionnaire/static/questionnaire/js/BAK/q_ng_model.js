/* q_model.js */
/* angular app for dealing w/ QModel forms */

(function() {
    var app = angular.module("q_model", ["q_base"]);
    //app.controller("QModelController", function() {
    app.controller("QModelController", [ "$http", "$log", function($http, $log) {

        var model_controller = this;
        model_controller.models = []; // initial data
        $http.get("/api/models", {format: "json"})
            .success(function(data) {
                model_controller.models = data;
            })
            .error(function(data) {

            });




    }]);

    app.controller("ReviewController", function() {
        this.review = {};
        this.addReview = function(model) {
            model.reviews.push(this.review);
            this.review = {};
        };
    });

    app.controller("PropertyController", function() {
        this.property = {};
        this.addProperty = function(model) {
            model.standard_properties.push(this.property);
            this.property = {};
        };
    });

    app.directive("modelTitle", function() {
       return {
         restrict: "E",
           templateURL: "ng_model_title.html"
       };
    });


})();

