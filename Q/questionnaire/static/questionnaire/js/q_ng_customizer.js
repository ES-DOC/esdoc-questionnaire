/* q_ng_customizer.js */
/* ng app for dealing w/ QCustomizations */

(function() {
    var app = angular.module("q_customizer", ["q_base", "ngCookies", "ui.bootstrap", "ui.sortable", "ng.django.forms"]);

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

    /***************/
    /* CONTROLLERS */
    /***************/

    /************************/
    /* top level controller */
    /************************/

    app.controller("CustomizerController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        /* TODO: DELETE THIS ONCE EVERYTHING WORKS */
        $scope.print_stuff = function() {
            /* print the current state of stuff */
            console.log("session_key=" + session_key);
            console.log($global_services.getModelFromPath("_DATA"));
        };

        /* setup the urls to use for AJAX */
        $scope.reset_urls = function() {
            $scope.api_url = api_url_dirname;
            $scope.view_url = view_url_dirname;
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
            /* if this is a new customization, the url will need to be changed to get the already cached serialization */
            $global_services.load(
                $scope.api_url + "cache/?session_key=" + session_key
            )
        }
        /* those were asynchronous calls */
        /* that's okay; the other controllers use a watch on $global_services.isLoaded() before loading their local variables */

       $scope.submit_customization = function() {

            $global_services.setBlocking(true);
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
                /* this line is NOT needed; I'm not simulating form data, I'm passing pure JSON */
                /*headers: {'Content-Type': 'application/x-www-form-urlencoded'},*/
                url: $scope.api_url,
                data: model
            })
            .success(function(data) {

                /* I have to explicitly re-set 'id' & 'name' based on data b/c 'id' is not bound to an ng form element */
                customization_id = data.id;
                customization_name = data.name;

                if (old_customization_name != customization_name) {
                    $scope.reset_urls();
                    window.location = $scope.view_url;
                    /* TODO: I SHOULD UPDATE THE LOCATION "PROPERLY" */
                    /* TODO: W/ "$scope.apply($location.path($scope.view_url))" */
                    /* TODO: BUT THAT REQUIRES SETTING UP ROUTES */
                }
                else {
                    /* if I "load" a new page as a result of submission, */
                    /* then the Django messaging framework will have a msg waiting for me */
                    /* otherwise, display a standard "success" msg here */
                    show_msg("Successfully saved customization", "success");
                }

            })
            .error(function(data) {
                /* just in case this is an unexpected server error, log the content */
                console.log(data);

                /* TODO: DEAL W/ SERVER ERRORS IN DATA; MAP TO FORMS */
                /* TODO: I KNOW THAT THE ONLY SERVER ERRORS CAN BE ON THE PARENT FORM, CUSTOMIZATION SECTION */
                /* TODO: (THEY ARE INVALID "name" & INVALID "is_default") */
                /* TODO: HOWEVER, I'LL STILL HAVE TO SOLVE THE GENERAL CASE FOR THE EDITING FORMS */

                show_msg("Error saving customization", "error");
            })
            .finally(function() {
                $global_services.setBlocking(false);
            });
        };

    }]);

    /*******************************/
    /* controller for a (sub)model */
    /*******************************/

    app.controller("ModelCustomizerController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        /* check the arguments */
	    if (!$attrs.currentModelPath == !$attrs.currentModel) {
            /* '(!x == !x)' simulates XOR; one and only one attr is required */
  	        throw new Error("ModelCustomizerController needs either the current_model or the current_model_path")
        };

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(function() { return $global_services.isLoaded(); },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    if ($attrs.currentModelPath) {
                        $scope.current_model_path = $attrs.currentModelPath;
                        $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                    }
                    else if ($attrs.currentModel) {
                        throw new Error("ModelCustomizerController CANNOT SUPPORT 'current_model' ATTRIBUTE YET");
                        $scope.current_model = $attrs.currentModel;
                        $scope.current_model_path = $global_services.getPathFromModel($attrs.currentModel);
                    }
                    $scope.is_loaded = true;
                }
            }
        );

        $scope.original_name = "";

        $scope.server_errors = {};

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

        /* some useful fns */

        $scope.get_model_by_attrs = function(models, attrs) {
            var model = $filter('filter')(
                models,
                attrs
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
            var subform_id = target_model.key + "_subform";
            var ancestor_subform = get_ancestor_element_by_id($event.target, subform_id);
            if (ancestor_subform.length) {
                msg = "This is a recursive relationship; The target model customization has already been specified."
                show_msg(msg);
            }
            else {
                target_model.display_detail = true;
            }
        };

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
                /* TODO: THIS IS CONFUSING B/C AT SOME POINT THE SERIALIZATION "BOTTOMS OUT" AND THERE ARE NO MORE "categories" OR "properties" */
                /* TODO: THAT IS BY DESIGN THOUGH, TO AVOID INFINITE RECURSION */
                /* TODO: THOSE "EMPTY" CUSTOMIZATIONS ARE NEVER MANIPULATED BY THIS FORM B/C A PARENT'S KEY WILL BE FOUND 1ST */
                /* TODO: BY THE LOAD-ON-DEMAND PARADIGM */
                /* TODO: WHY ARE THEY EVEN CREATED, THOUGH? */
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


        $scope.update_names2 = function(new_name, model) {
            if (typeof model == "undefined" || model === null) {
    	        /* default value */
                model = $global_services.getData();
            }
            /* only update valid names */
            if (typeof new_name != "undefined") {
//                /* and only update changed names */
//                if (new_name != $scope.original_name) {

                    console.log("looking at " + model.model_title);

                    /* ('model.name' will already have been changed) */

                    /* change any categories */
                    $.each(model.categories, function (i, category) {
                        category.name = new_name;
                    });

                    /* change any properties */
                    $.each(model.properties, function(i, property) {
                        property.name = new_name;
                        $.each(property.relationship_target_model_customizations, function(i, target_model) {
                            /* and do the same recursively for any subform customizations */
                            console.log("looking at " + target_model.model_title);
                            target_model.name = new_name;
                            $scope.update_names(new_name, target_model);
                        });
                    });

                    /* reset the original_name for next time */
                    $scope.original_name = new_name;
                }
//            }
        };

    }]);

    /***********/
    /* THE END */
    /***********/

})();