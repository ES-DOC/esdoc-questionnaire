/* q_ng_customize.js */
/* ng app for dealing w/ QCustomizations */

(function() {
    var app = angular.module("q_customize", ["q_base", "ngCookies", "ui.bootstrap", "ui.sortable", "djng.forms"]);

    /**********/
    /* CONFIG */
    /**********/

    app.config(['$httpProvider', '$provide', function($httpProvider, $provide) {

        /* TODO: MOVE THIS AJAX LOGIC INTO q_base */
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

        /* I have to admit to not fully understanding how this code works */
        /* but it allows uibAccordion to work w/ ui-sortable */
        /* (https://stackoverflow.com/questions/26520131/how-can-i-create-a-sortable-accordion-with-angularjs/27637542#27637542) */
        $provide.decorator('uibAccordionDirective', function($delegate) {
           var directive = $delegate[0];
            directive.replace = true;
            return $delegate;
        });

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

    app.controller("CustomizerController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        /* $scope.server_errors['form_name']['field_name'] is used to store server errors */
        /* the placeholder for this info is created in QForm.add_custom_errors() line #224 */
        /* and that gets populated as needed in $scope.submit_customization below */
        $scope.server_errors = {};

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        /* setup the urls to use for AJAX */
        /* this can be called multiple times as a fn */
        /* in case the id or name changes (after saving) */
        $scope.reset_urls = function() {
            $scope.api_url = api_url_dirname + "/";
            $scope.view_url = view_url_dirname + "/";
            if (customization_id) {
                $scope.api_url = $scope.api_url + customization_id + "/";
                $scope.view_url = $scope.view_url + customization_name + "/";
            }
        };
        $scope.reset_urls();

        /* now load initial JSON data (using the above urls) */
        if (customization_id) {
            /* if this is an existing customization, the url will be normal */
            $global_services.load($scope.api_url);
        }
        else {
            /* if this is a new customization, the url will need to be changed to get the cached serialization */
            $global_services.load(
                $scope.api_url + "cache/?session_key=" + session_key
            )
        }

        /* those were asynchronous calls */
        /* that's okay; the other controllers use a watch on $global_services.isLoaded() before loading local variables */

        $scope.submit_customization = function(form_to_render_server_errors) {
            $global_services.setBlocking(true);

            var form_name = form_to_render_server_errors.$name;
            $scope.server_errors[form_name] = {};  /* reset any existing server errors */

            var model = $global_services.getData();
            var old_customization_name = customization_name;

            if (customization_id) {
                /* updating an existing customization */
                var request_method = "PUT";
            }
            else {
                /* creating a new customization */
                var request_method = "POST";
            }

            $http({
                method: request_method,
                url: $scope.api_url,
                data: model
            })
            .success(function(data) {
                /* I have to explicitly re-set 'id' & 'name' based on data */
                customization_id = data.id;
                customization_name = data.name;

                if (old_customization_name != customization_name) {
                    $scope.reset_urls();
                    window.location = $scope.view_url;
                    /* TODO: I SHOULD UPDATE THE LOCATION "PROPERLY" */
                    /* TODO: W/ "$scope.apply($location.path($scope.view_url))" */
                    /* TODO: BUT THAT REQUIRES SETTING UP ROUTES, WHICH MAY BE MORE TROUBLE THAN IT'S WORTH */
                }
                else {
                    /* the above branch automatically gets a pending msg by virtue of the new page load */
                    /* in this branch, I have to manually check for a pending msg b/c I don't reload the page */
                    check_msg();
                }
            })
            .error(function(data) {
                /* just in case this is an unexpected server error, log the content */
                console.log(data);
                /* but if I'm in this loop, I'm really expecting a (handled) validation error */
                /* TODO: MOVE THIS TO A GLOBAL SCOPE */
                $.each(data, function(field, errors) {
                    /* (and only render errors for fields that are actually displayed on the form) */
                    /* (recall that the errors get generated from the serializer but rendered in the form) */
                    if (form_to_render_server_errors.hasOwnProperty(field)) {
                        form_to_render_server_errors[field].$setValidity('server', false);
                        console.log("the field is (from submit_customization):");
                        console.log(form_to_render_server_errors[field]);
                        form_to_render_server_errors[field].$setDirty();
                        $scope.server_errors[form_name][field] = errors.join(", ");
                    }
                });

                /* TODO: DEAL W/ SERVER ERRORS IN DATA; MAP TO FORMS */
                /* TODO: I KNOW THAT THE ONLY SERVER ERRORS CAN BE ON THE TOP_LEVEL_FORM */
                /* TODO: HOWEVER, I STILL OUGHT TO SOLVE THE GENERAL CASE WHEN DEALING W/ MULITIPLE FORMS */

                show_msg("Error saving customization", "error");
            })
            .finally(function() {
                $global_services.setBlocking(false);
            });
        };

        $scope.print_stuff = function() {
            /* print the current state of stuff */
            console.log("session_key=" + session_key);
            console.log($global_services.getModelFromPath("_DATA"));
        };

    }]);

    /*******************************/
    /* controller for a (sub)model */
    /*******************************/

    app.controller("ModelCustomizerController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(function() { return $global_services.isLoaded() },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    $scope.current_model_path = $attrs.currentModelPath;
                    $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                    $scope.is_loaded = true;
                    console.log("my current_model: ");
                    console.log($scope.current_model);
                }
            }
        );

        $scope.original_name = "";

        $scope.models_validity = true;

        $scope.categories_validity = true;
        $scope.categories_sortable_options = $.extend(true,
            {
                axis: 'x'
                //handle: '.sortable_handle',
                //placeholder: 'sortable_item',
            },
            $global_services.getSortableOptions()
        );

        $scope.properties_validity = true;
        $scope.properties_sortable_options = $.extend(true,
            {
                axis: 'y',
                handle: '> .panel-heading'  /* ng seems to replace my ".accordion_header" w/ "panel-heading" at some point */
                //placeholder: 'sortable_item',
            },
            $global_services.getSortableOptions()
        );

        /* purposefully not using a $watch to call this fn */
        /* using "ng-blur" (defined in forms_customization_models.py) instead */
        /* to make it 1) easy to test, and 2) responsive to explicit user input only */
        /* the general consensus is that "ng-update" is more efficient than "$watch" anyway */
        $scope.update_names = function(new_name, model) {

            if (typeof model == "undefined" || model === null) {
    	        /* default value */
                model = $global_services.getData();
            }

            /* only update valid names */
            if (typeof new_name != "undefined") {

                /* change the model */
                /* (the 1st time this is called, it will already have been changed) */
                model.name = new_name;

                /* change any categories */
                if ("categories" in model) {
                    $.each(model.categories, function (i, category) {
                        category.name = new_name;
                    });
                }

                /* change any properties */
                if ("properties" in model) {
                    $.each(model.properties, function (i, property) {
                        property.name = new_name;
                        $.each(property.relationship_target_model_customizations, function (i, subform_model_customization) {
                            $scope.update_names(new_name, subform_model_customization);
                        });
                    });
                }
            }
        };

        /* some useful helper fns */

        $scope.get_model_by_attrs = function(models, attrs) {
            var model = $filter('filter')(
                models, attrs
            )[0];
            return model;
        };

        $scope.get_model_by_index = function(models, index) {
            return models[index];
        };

        $scope.expand_properties = function() {
            var properties = $scope.current_model.properties;
            for(var i=0; i < properties.length; i++) {
                properties[i].display_detail = true;
            }
        };

        $scope.collapse_properties = function() {
            var properties = $scope.current_model.properties;
            for(var i=0; i < properties.length; i++) {
                properties[i].display_detail = false;
            }
        };

        $scope.view_all_categories_properties = function() {
            var categories = $scope.current_model.categories;
            for (var i=0; i<categories.length; i++) {
                categories[i].display_properties = true;
            }
        };

        $scope.display_subform_for_target_model = function($event, target_model) {
            /* check if an ancestor subform already exists */
            var ancestor_subform = $($event.target).closest("#" + target_model.key + "_subform");
            if (ancestor_subform.length) {
                msg = "This is a recursive relationship; The target model customization has already been specified."
                show_msg(msg);
            }
            else {
                target_model.display_detail = true;
            }
        };

    }]);

    /***********/
    /* THE END */
    /***********/

})();