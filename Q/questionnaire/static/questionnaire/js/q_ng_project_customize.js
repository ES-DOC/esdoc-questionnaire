/* q_ng_project_customize.js */
/* ng app for dealing w/ QProjects */

/* TODO: CONSOLIDATE "q_project.js" & "q_project_customize.js" & "q_project_manage.js" */

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
    /* except for the built-in scope fns (like $watch, $apply, etc.) */
    /* so I include it and use it in rare occasions */
    /* see http://toddmotto.com/digging-into-angulars-controller-as-syntax/ */

    app.controller("ProjectController", [ "$http", "$global_services", "$filter", "$window", "$scope", function($http, $global_services, $filter, $window, $scope) {

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        /* look here - I am passing "project_id" to this controller */
        /* it is used throughout the code, as a query parameter to the DRF API */
        /* this is a global variable in the template (set via Django) */
        /* I don't think that this is the "ng-approved" way of doing things */
        /* see: http://stackoverflow.com/questions/14523679/can-you-pass-parameters-to-an-angularjs-controller-on-creation */

        var project_controller = this;

        project_controller.project = {};

        project_controller.possible_document_types = [];
        project_controller.selected_document_type = null;

        project_controller.documents = [];
        project_controller.filtered_documents = [];
        project_controller.paged_documents = [];
        project_controller.total_documents = 0;
        project_controller.current_document_page = 0;
        project_controller.document_page_size = 6;
        project_controller.document_paging_size = 10;

        this.load_project = function() {
            $global_services.setBlocking(true);
            $http.get("/api/projects_test/" + project_id, {format: "json"})
                .success(function (data) {
                    project_controller.project = data;
                    project_controller.possible_document_types = data["document_types"];
                })
                .error(function (data) {
                    console.log(data);
                })
                .finally(function() {
                    $global_services.setBlocking(false);
                });
        };

        this.load_documents = function() {
            $global_services.setBlocking(true);
            $http.get("/api/customizations_lite/?project=" + project_id, {format: "json"})
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
                    /* filter and page them as needed */
                    project_controller.update_filters();
                    project_controller.update_paging();
                })
                .error(function (data) {
                    console.log(data);
                })
                .finally(function() {
                    $global_services.setBlocking(false);
                });

        };

        project_controller.load_project();
        project_controller.load_documents();

        this.update_filters = function() {
            /* I could use the built-in ng $filter framework, but that just seems like overkill */
            if (project_controller.selected_document_type == null) {
                project_controller.filtered_documents = project_controller.documents;
            }
            else {
                project_controller.filtered_documents = $.map(project_controller.documents, function(document, index) {
                    if (document.proxy_name == project_controller.selected_document_type.name) {
                        return document;
                    }
                });
            }
            project_controller.total_documents = project_controller.filtered_documents.length;
        };

        this.update_paging = function() {
            /* so paging mostly happens via the "uib-pagination" class and a $watch on "current_document_page" */
            /* however, when I change the sorting order I go ahead and manually re-sort the entire "documents" array */
            /* and then re-page that; this prevents me from only sorting the currently paged set of documents */
            /* (there are probably better ways to do this, but I don't care) */
            var start = (project_controller.current_document_page - 1) * project_controller.document_paging_size;
            var end = project_controller.current_document_page * project_controller.document_paging_size;
            project_controller.paged_documents = project_controller.filtered_documents.slice(start, end);
            project_controller.document_page_start = start;
            project_controller.document_page_end = end > project_controller.total_documents ? project_controller.total_documents : end;
        };

        $scope.$watch("project_controller.current_document_page", function() {
            project_controller.update_paging();
        });

        $scope.$watch("project_controller.selected_document_type", function(old_selected_document_type, new_selected_document_type) {
            if (old_selected_document_type != new_selected_document_type) {
                project_controller.update_filters();
                project_controller.update_paging();
            }
        });

        this.create_document_type = function() {
            var create_document_type_url = "/" + project_name + "/customize/" + project_controller.selected_document_type.ontology + "/" + project_controller.selected_document_type.name;
            $window.open(create_document_type_url, '_blank');
        };

        project_controller.document_sort_type = "label";
        project_controller.document_sort_reverse = false;

        this.change_document_sort_type = function(sort_type) {
            if (project_controller.document_sort_type != sort_type) {
                project_controller.document_sort_type = sort_type;
                project_controller.document_sort_reverse = false;
            }
            else {
                project_controller.document_sort_reverse = !(project_controller.document_sort_reverse);
            }
            /* not only do we change the sorting, we also have to re-page things - see the comment above on "update_paging()" */
            project_controller.documents = $filter('orderBy')(project_controller.documents, sort_type, project_controller.document_sort_reverse);
//            project_controller.update_filters();
            project_controller.update_paging();
        };

        this.customization_delete = function(customization) {
            var msg = "This will permanently delete this customization.  Are you sure you wish to continue?"
            bootbox.confirm(msg, function(result) {
                if (! result) {
                    show_lil_msg("Good thinking.");
                }
                else {
                    $global_services.setBlocking(true);
                    var customization_delete_request_url = "/services/customization_delete/";
                    var customization_delete_request_data = $.param({
                        "customization_id": customization.id
                    });
                    $http({
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        url: customization_delete_request_url,
                        data: customization_delete_request_data
                    }).success(function(data) {
                        project_controller.load_documents();
                        check_msg();
                    })
                    .error(function(data) {
                        console.log(data);
                        check_msg();
                    })
                    .finally(function() {
                        $global_services.setBlocking(false);
                    });
                }
            });
        };

        this.print_stuff = function() {
            console.log(project_controller.filtered_documents);
            console.log(project_controller.selected_document_type);
        };

    }]);

    /***********/
    /* THE END */
    /***********/

})();