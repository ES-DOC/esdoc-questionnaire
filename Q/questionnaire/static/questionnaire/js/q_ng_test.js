/* q_ng_project.js */
/* ng app for dealing w/ QProjects */

(function() {
    var app = angular.module("q_project", ["q_base"]);

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

    /* don't generally need $scope for ng > 1.3 */
    /* except for the built-in scope fns (like $watch, etc.) */
    /* so I include it and use it in rare occasions */
    /* see http://toddmotto.com/digging-into-angulars-controller-as-syntax/ */

    app.controller("ProjectController", [ "$http", "$global_services", "$filter", "$window", "$scope", function($http, $global_services, $filter, $window, $scope) {

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        /* look here - I am passing "project_id" to this controller */
        /* it is used throughout the code, as a query parameter to the DRF API */
        /* this is a global variable in the template (set via Django) */
        /* I don't think that this is the "AngularJS-Approved" way of doing things */
        /* see: http://stackoverflow.com/questions/14523679/can-you-pass-parameters-to-an-angularjs-controller-on-creation */

        var project_controller = this;

        project_controller.project = {};

        project_controller.possible_document_types = [];
        project_controller.selected_document_type = null;

        project_controller.documents = [];
        project_controller.paged_documents = [];
        project_controller.total_documents = 0;
        project_controller.current_document_page = 0;
        project_controller.document_page_size = 6;
        project_controller.document_paging_size = 10;

        $scope.$watch("project_controller.current_document_page", function() {
            var start = (project_controller.current_document_page - 1) * project_controller.document_paging_size;
            var end = project_controller.current_document_page * project_controller.document_paging_size;

            project_controller.paged_documents = project_controller.documents.slice(start, end);
            project_controller.document_page_start = start;
            project_controller.document_page_end = end > project_controller.total_documents ? project_controller.total_documents : end;
        });

        this.load = function() {

            /* get the project info (including which document_types are supported) */
            $http.get("/api/projects_test/" + project_id, {format: "json"})
                .success(function (data) {
                    project_controller.project = data;
                    project_controller.possible_document_types = data["document_types"];
                })
                .error(function (data) {
                    console.log(data);
                });

            /* get the existing documents info */
            $http.get("/api/realizations_lite/?project=" + project_id, {format: "json"})
                .success(function (data) {
                    console.log(data);
                    project_controller.documents = data.results;
                    project_controller.total_documents = data.count;
                    project_controller.current_document_page = project_controller.total_documents > 0 ? 1 : 0;
                    $.each(project_controller.documents, function(i, d) {
                        if (d.synchronization.length) {
                            project_controller.has_unsynchronized_document = true;
                        }
                        if (!d.is_complete) {
                            project_controller.has_incomplete_document = true;
                        }
                        if (project_controller.has_unsynchronized_document && project_controller.has_incomplete_document) {
                            return false;  // break out of the loop if we've already found matches
                        }
                    });
                })
                .error(function (data) {
                    console.log(data);
                });

        };

        project_controller.load();

        $scope.$watch("project_controller.selected_document_type", function(old_selected_document_type, new_selected_document_type) {
            if (old_selected_document_type != new_selected_document_type) {
                console.log("I AM HERE");
            }
        });

        this.create_document_type = function() {
            var create_document_type_url = "/edit/" + project_controller.selected_document_type.ontology + "/" + project_controller.selected_document_type.name;
            console.log("about to goto: " + create_document_type_url)
            $window.open(create_document_type_url, '_blank');
        };

        project_controller.document_sort_type = "label";
        project_controller.document_sort_reverse = false;

        this.change_document_sort_type = function(sort_type) {
            project_controller.document_sort_type = sort_type;
            project_controller.document_sort_reverse = !(project_controller.document_sort_reverse);
        };

        this.print_stuff = function() {
            console.log(project_controller.document_sort_type);
            console.log(project_controller.selected_document_type);

        };


    }]);

    /***********/
    /* THE END */
    /***********/

})();