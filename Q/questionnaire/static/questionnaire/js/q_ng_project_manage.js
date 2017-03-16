/* q_ng_project.js */
/* ng app for dealing w/ QProjects */

(function() {
    var app = angular.module("q_project_manage", ["q_base"]);

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

    app.controller("ProjectManageController", [ "$http", "$global_services", "$scope", function($http, $global_services, $scope) {

        $scope.server_errors = {};

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        /* look here - I am passing "project_id" to this controller */
        /* it is used throughout the code, as a query parameter to the DRF API */
        /* this is a global variable in the template (set via Django) */
        /* I don't think that this is the "AngularJS-Approved" way of doing things */
        /* see: http://stackoverflow.com/questions/14523679/can-you-pass-parameters-to-an-angularjs-controller-on-creation */

        var project_controller = this;

        project_controller.project_validity = true;
        project_controller.project = {};

        this.load = function() {
            $http.get("/api/projects/" + project_id, {format: "json"})
                .success(function (data) {
                    project_controller.project = data;
                    project_controller.saved_project_title = data.title;
                })
                .error(function (data) {
                    console.log(data);
                });
        };
        project_controller.load();

        this.is_project_user = function(user) {
            return $.inArray(this.project.user_group_name, user.groups) >= 0;
        }

        this.is_project_member = function(user) {
            return $.inArray(this.project.member_group_name, user.groups) >= 0;
        }

        this.is_project_admin = function(user) {
            return $.inArray(this.project.admin_group_name, user.groups) >= 0;
        }

        this.approve_pending_member = function(user) {
            $global_services.setBlocking(true);
            var approve_project_member_url = "/services/" + this.project.name + "/project_add_member/";
            var approve_project_member_data = $.param({
                "user_id": user.id
            });

            $http({
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                url: approve_project_member_url,
                data: approve_project_member_data
            }).success(function(data) {
                var user_index = project_controller.project.pending_users.indexOf(user);
                project_controller.project.pending_users.splice(user_index, 1)
                project_controller.project.users.push(data)
                show_msg("Successfully added user to project", "success");
            })
            .error(function(data) {
                console.log(data);
                check_msg();
            })
            .finally(function() {
                $global_services.setBlocking(false);
            });
        }

        this.submit_project = function(form_to_render_server_errors) {
            $global_services.setBlocking(true);

            var form_name = form_to_render_server_errors.$name;
            $scope.server_errors[form_name] = {};  /* reset any existing server errors */

            var submit_project_url ="/api/projects/" + project_id;
            console.log(submit_project_url);
            $http({
                method: "PUT",
                url: submit_project_url,
                data: project_controller.project
            })
            .success(function(data) {
                project_controller.saved_project_title = data.title;
                show_msg("Successfully updated project.", "success");
            })
            .error(function(data) {
                /* just in case this is an unexpected server error, log the content */
                console.log(data);
                /* but if I'm in this loop, I'm really expecting a (handled) validation error */
                $.each(data, function(field, errors) {
                    /* (and only render errors for fields that are actually displayed on the form) */
                    /* (recall that the errors get generated from the serializer but rendered in the form) */
                    if (form_to_render_server_errors.hasOwnProperty(field)) {
                        form_to_render_server_errors[field].$setValidity('server', false);
                        form_to_render_server_errors[field].$setDirty();
                        $scope.server_errors[form_name][field] = errors.join(", ");
                    }
                });
                show_msg("Error saving customization", "error");
            })
            .finally(function() {
                $global_services.setBlocking(false);
            });
        };

        this.print_stuff = function() {
            console.log(this.project);
        };

    }]);

    /***********/
    /* THE END */
    /***********/

})();