/* q_model.js */
/* angular app for dealing w/ QProjects */

(function() {
    var app = angular.module("q_project", ["q_base", "ngCookies"]);

    app.config(['$httpProvider', function($httpProvider) {

        /* TODO: MOVE THIS AJAX LOGIC INTO q_base */
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    }]);

    /* don't generally need $scope for ng > 1.3 */
    /* except for the built-in scope fns (like $watch, etc.) */
    /* so I include it and use it in rare occasions */
    /* see http://toddmotto.com/digging-into-angulars-controller-as-syntax/ */

    app.controller("ProjectController", [ "$http", "$cookies", "$scope", function($http, $cookies, $scope) {

        /* look here, I am passing "project_id" to this controller */
        /* it is used throughout the code, as a query parameter to the RESTful API */
        /* this is a global variable in the template (set via Django) */
        /* I don't think that this is the "AngularJS-Approved" way of doing things */
        /* see: http://stackoverflow.com/questions/14523679/can-you-pass-parameters-to-an-angularjs-controller-on-creation */

        /* TODO: MOVE THIS CSRF LOGIC INTO q_base */
        //$http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
        //$http.defaults.headers.post['X-XSRFToken'] = $cookies.csrftoken;


        var project_controller = this;

        project_controller.project = {};  // initial data
        project_controller.documents = []; // initial data
        project_controller.customizations = []; // initial data
        project_controller.ontologies = []; // initial data (includes proxies)

        project_controller.selected_document_ontology = {};
        project_controller.selected_document_proxy = {};
        project_controller.selected_customization_ontology = {};
        project_controller.selected_customization_proxy = {};

        project_controller.customization_sort_type = "name";
        project_controller.customization_sort_reverse = false;
        project_controller.document_sort_type = "label";
        project_controller.document_sort_reverse = false;


        project_controller.has_default_customization = false;
        project_controller.has_unsynchronized_customization = false;
        project_controller.has_unsynchronized_document = false;
        project_controller.has_incomplete_document = false;

        /* after all this work to get $watch working, it turns out not to fire for selects */
        /* so I just bind ng-select to the fns below */
        //$scope.$watch(project_controller.selected_document_ontology, function(new_val, old_val) {
        //});

        this.selected_document_ontology_changed = function() {
            project_controller.selected_document_proxy = {};
            $("#document_proxy").addClass("q-dirty");
            /* disable the link w/ extreme prejudice */
            $('#create_document').addClass('btn-disabled');
            $('#create_document').attr('disabled', 'disabled');
            $('#create_document').prop('disabled', true);
            $('#create_document').click(function(e) {
                e.preventDefault();
            });
        };

        this.selected_document_proxy_changed = function() {
            $("#document_proxy").removeClass("q-dirty");
            /* re-enable the link */
            $('#create_document').removeClass('btn-disabled');
            $('#create_document').removeAttr('disabled');
            $('#create_document').prop('disabled', false);
            $('#create_document').unbind('click').click();
        };


        this.selected_customization_ontology_changed = function() {
            project_controller.selected_customization_proxy = {};
            /* disable the link w/ extreme prejudice */
            $('#create_customization').addClass('btn-disabled');
            $('#create_customization').attr('disabled', 'disabled');
            $('#create_customization').prop('disabled', true);
            $('#create_customization').click(function(e) {
                e.preventDefault();
            });
        };

        this.selected_customization_proxy_changed = function() {
            /* re-enable the link */
            $('#create_customization').removeClass('btn-disabled');
            $('#create_customization').removeAttr('disabled');
            $('#create_customization').prop('disabled', false);
            $('#create_customization').unbind('click').click();
        };

        this.change_document_sort_type = function(sort_type) {
            project_controller.document_sort_type = sort_type;
            project_controller.document_sort_reverse = !(project_controller.document_sort_reverse);
        };

        this.change_customization_sort_type = function(sort_type) {
            project_controller.customization_sort_type = sort_type;
            project_controller.customization_sort_reverse = !(project_controller.customization_sort_reverse);
        };

        this.load = function() {
            $http.get("/api/projects/" + project_id, {format: "json"})
                .success(function (data) {
                    project_controller.project = data;
                })
                .error(function (data) {
                    console.log(data);
                });

            $http.get("/api/models_lite/?project=" + project_id, {format: "json"})
                .success(function (data) {
                    project_controller.documents = data.results;
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

            $http.get("/api/customizations_lite/?ordering=name&project=" + project_id, {format: "json"})
                .success(function (data) {
                    project_controller.customizations = data.results;
                    $.each(project_controller.customizations, function(i, c) {
                        if (c.synchronization.length) {
                            project_controller.has_unsynchronized_customization = true;
                        }
                        if (c.is_default) {
                            project_controller.has_default_customization = true;
                        }
                    });
                })
                .error(function (data) {
                    console.log(data);
                });

            $http.get("/api/ontologies/?ordering=key&is_registered=true", {format: "json"})
                .success(function (data) {
                    var ontologies = data.results;
                    project_controller.ontologies = ontologies;
                    project_controller.selected_document_ontology = ontologies[0];
                    project_controller.selected_document_proxy = ontologies[0].document_types[0];
                    project_controller.selected_customization_ontology = ontologies[0];
                    project_controller.selected_customization_proxy = ontologies[0].document_types[0];

                })
                .error(function (data) {
                    console.log(data);
                });
        };

        project_controller.load();

        this.document_publish = function(document) {
            var publish_document_request_url = "/services/document_publish/";
            var publish_document_request_data = $.param({
                "document_id": document.id
            });

            /* TODO: THIS IS ALL A BIT UNINTUITIVE */
            /* WHY IS IT SO HARD TO PASS POST DATA */
            /* IN AngularJS OUTSIDE OF A FORM?!? */
            $http({
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                url: publish_document_request_url,
                data: publish_document_request_data
            }).success(function(data) {

                project_controller.load();

                check_msg();

            })
            .error(function(data) {
                console.log(data);
                check_msg();
            });


        };

        this.project_join_request = function(user_id) {
            var project_join_request_url =
                "/services/" + project_controller.project.name +
                "/project_join_request/";
            var project_join_request_data = $.param({
                user_id: user_id
            });

            /* TODO: THIS IS ALL A BIT UNINTUITIVE */
            /* WHY IS IT SO HARD TO PASS POST DATA */
            /* IN AngularJS OUTSIDE OF A FORM?!? */
            $http({
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                url: project_join_request_url,
                data: project_join_request_data
            }).success(function(data) {
                check_msg();
            })
            .error(function(data) {
                console.log(data);
                check_msg();
            });

        };

        this.customization_delete = function(customization) {
            var msg = "This will permanently delete this customization.  Are you sure you wish to continue?"
            bootbox.confirm(msg, function(result) {
                if (! result) {
                    show_lil_msg("Good thinking.");
                }
                else {

                    var customization_delete_url = "/services/customization_delete/";
                    var customization_delete_data = $.param({
                        "customization_id": customization.id
                    });

                    /* TODO: THIS IS ALL A BIT UNINTUITIVE */
                    /* WHY IS IT SO HARD TO PASS POST DATA */
                    /* IN AngularJS OUTSIDE OF A FORM?!? */
                    $http({
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        url: customization_delete_url,
                        data: customization_delete_data
                    }).success(function(data) {

                        //$.each(project_controller.customizations, function(i, c) {
                        //   if (c.id == customization.id)  {
                        //       delete project_controller.customizations[i];
                        //   }
                        //});

                        project_controller.load();

                        check_msg();
                    })
                    .error(function(data) {
                        console.log(data);
                        check_msg();
                    });
                }
            });
        };

        this.customization_synchronize = function(customization) {
            var msg = "This will automatically update the customization so that it is compatible with the current set of ontologies and vocabularies associated with this project.  There may be unexpected results.  Are you sure you wish to continue?";
            bootbox.confirm(msg, function(result) {
                if (!result) {
                    show_lil_msg("Maybe next time.");
                }
                else {
                    alert("TODO!")
                }
            });
        }

    }]);

})();

