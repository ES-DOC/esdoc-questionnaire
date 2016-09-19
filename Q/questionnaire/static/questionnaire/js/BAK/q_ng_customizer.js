/* q_ng_customizer.js */
/* ng app for dealing w/ QCustomizations */

(function() {
    var app = angular.module("q_customizer", ["q_base", "ngCookies", "ui.bootstrap", "ui.sortable", "ng.django.forms"]);

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

    app.controller("CustomizerController", [ "$scope", "$http", "$cookies", '$location', '$filter', function($scope, $http, $cookies, $location, $filter) {

        /* set initial data */
        $scope.is_default_model_customization = false;
        $scope.model_customization = { };
        $scope.server_errors = {};
        $scope.total_validity = true;
        $scope.models_validity = true;
        $scope.categories_validity = true;
        $scope.properties_validity = true;

        $scope.foo = null;

        $scope.non_modifying_sortable_options = {
            /* this is used as a base to build up other sortable_options */
            /* it includes the very HARD but really CLEVER code which allows */
            /* the sorted items to have their "order" attribute changed */
            /* w/out actually changing their order in the javascript array */
            /* (this is required for the load-on-demand paradigm to work) */
            /* (I need to know _which_ model in the list to retrieve) */
            containment: "parent",  /* prevent overflows */
            helper : 'clone',  /* this awesome lil hack prevents sorting from firing the click event */
            start: function (e, ui) {
                ui.placeholder.height(ui.item.height());
                ui.placeholder.width(ui.item.width());
            },
            stop: function(e, ui) {
                /* I AM NO LONGER DOING THIS */
                /* THIS ASSUMES THAT THE ORDER OF ELEMENTS IN THE NG ARRAY ACTUALLY CHANGES */
                /* BUT I PREVENT THAT IN "update" BELOW */
                /* B/C THE ORDER MUST STAY THE SAME SO THAT ANY FORMS I RETRIEVE VIA AJAX */
                /* HAVE THE CORRECT INDEX */
                //var sorted_properties = ui.item.sortable.sourceModel;
                //$.each(sorted_properties, function(i, property) {
                //    property.order = i+1;
                //});
            },
            update: function(e, ui) {
                /* THIS WAS HARD! */
                /* I MAKE AN ARRAY OF INDICES WHICH I RE-ORDER AS IF THAT WERE THE ARRAY BEING SORTED */
                /* (USING THE "splice" FN) */
                /* I THEN UPDATE THE "order" ATTRIBUTE OF THE NG ARRAY BASED ON THAT RE-ORDERED INDEX ARRAY */

                var models = ui.item.sortable.sourceModel;

                var old_index = ui.item.sortable.index;
                var new_index = ui.item.sortable.dropindex;

                var sorted_model_indices = sort_objects_by_attr(
                    $.map(models, function(obj, i) {
                            /* TODO: I CAN PROBABLY SIMPLIFY THIS; I ONLY NEED "index" */
                            return {"index": i, "order": obj.order }
                        }
                    ),
                    "order"
                );
                sorted_model_indices.splice(new_index, 0, sorted_model_indices.splice(old_index, 1)[0]);

                for (var i=0; i<sorted_model_indices.length; i++) {
                    models[sorted_model_indices[i].index].order = i + 1;
                }
                /* cancel the default behaviour; */
                /* this means do NOT re-sort the array bound via ng (see comment above); */
                /* the widgets will still be sorted, though, b/c of the "orderBy" filter used by ng */
                ui.item.sortable.cancel();

            }
        };

        $scope.category_customization_sortable_options = $.extend(true,
            {
                axis: 'x'
                //handle: '.sortable_handle',
                //placeholder: 'sortable_item',
            },
            $scope.non_modifying_sortable_options
        );

        $scope.property_customization_sortable_options = $.extend(true,
            {
                axis: 'y',
                handle: '> .panel-heading'  /* ng seems to replace my ".accordion_header" w/ "panel-heading" at some point */
                //placeholder: 'sortable_item',
            },
            $scope.non_modifying_sortable_options
        );

        $scope.expand_properties = function(properties) {
            for(var i=0; i < properties.length; i++) {
                properties[i].display_detail = true;
            }
        };

        $scope.collapse_properties = function(properties) {
            for(var i=0; i < properties.length; i++) {
                properties[i].display_detail = false;
            }
        };

        $scope.view_all_properties_with_categories = function(categories) {
            for (var i=0; i<categories.length; i++) {
                categories[i].display_properties = true;
            }
        };

        /* TODO: MOVE THESE NEXT 5 FNS TO q_ng_base.js */

        $scope.get_model_by_attrs = function(models, attrs) {
            var filtered_model = $filter('filter')(
                models,
                attrs
            )[0];
            return filtered_model;
        };

        $scope.get_models_by_attrs = function(models, attrs) {
            var filtered_models = $filter('filter')(
                models,
                attrs
            );
            return filtered_models;
        };

        $scope.get_model_by_string = function(string) {
            return $scope.$eval(string);
        };

        $scope.get_model_index = function(model, models) {
            /* returns the index of the "model" object in the "models" collection */
            return models.indexOf(model);
        };

        $scope.get_model_from_path = function(path) {
            /* returns a model for a given JSON "path" */
            return $scope.$eval(path);
        };
        
        $scope.get_path_from_model = function(obj, target, path) {
            /* returns a JSON "path" for a given model */
            /* (used to determine scope_prefix for forms */

            if (typeof path === "undefined" || path === null) {
                path = "model_customization";
            }

            for (var key in obj) {
                var value = obj[key];
                var value_type = value.constructor;

                /* value can either be an Array */
                if (value_type === Array) {
                    if (value === target) {
        	            return path + "." + key;
                    }
                    for (var i=0; i<value.length; i++) {
                        if (value[i] == target) {
                            return path + "." + key + "[" + i + "]";
                        }
                        var result = get_path_from_model(value, target, path + "." + key + "[" + i + "]");
                        if (result) {
                            return result;
                        }
                    }
                }

                /* or value can be an Object itself */
                else if (value_type === Object) {
                    if (value === target) {
        	            return path + "." + key;
                    }
                    var result = get_path(value, target, path);
                    if (result) {
                        return result;
                    }
                }

                /* or value can something atomic */
                else {
                    if (value === target) {
                        return path + "." + key;
                    }
                }

            }
            return false;
        };


        /* purposefully not using a $watch to call this fn */
        /* using "ng-change" (defined in forms_customization_models.py) instead */
        /* to make it 1) easy to test, and 2) responsive to explicit user input only */
        /* the general consensus is that "ng-change" is more efficient than "$watch" anyway */
        var subform_indicator_attr = "relationship_show_subform";
        var subform_customization_attr = "relationship_subform_customization";
        $scope.update_names = function(model, name_value) {
            /* set default values for the 1st time this recursive fn is called */
            model = typeof model !== 'undefined' ? model : $scope.model_customization;
            name_value = typeof name_value !== 'undefined' ? name_value : $scope.model_customization.name;

            var properties = model.properties;
            if (properties) {
                /* if this is called before ng finishes loading content */
                /* (which is possible), then properties will be undefined */
                /* if so the '$.each' fn below would fail so don't run it */
                /* this is okay b/c it would only happen upon 1st page load */
                /* in which case the name would not have had a chance to change */
                $.each(properties, function (i, property) {
                    if (property[subform_indicator_attr]) {
                        property[subform_customization_attr].name = name_value;
                        $scope.update_names(property[subform_customization_attr], name_value);
                    }
                });
            }

        };

        /* setup the URLs to use (to retrieve data) */
        $scope.set_urls = function() {
            $scope.api_url = api_url_dirname;
            $scope.view_url = view_url_dirname;
            if (customization_id) {
                $scope.api_url = $scope.api_url + customization_id + "/";
                $scope.view_url = $scope.view_url + customization_name + "/";
            }
        };

        /* (re)load data */
        $scope.load = function() {

            /* get the data from the API */
            if (customization_id) {
                /* if this is an existing customization */
                /* the url will be preset as "www.domain.com/api/customizations/<id>" */
                var api_get_url = $scope.api_url;
            }
            else {
                /* if this is a new customization */
                /* the base api url needs to be changed so that it gets the already cached customization: "www.domain.com/api/customizations/cache" */
                var api_get_url = $scope.api_url + "cache/?session_key=" + session_key;
            }

            $http.get(api_get_url, {format: "json"})
                .success(function (data) {
                    $scope.model_customization = data;
                    $scope.is_default_model_customization = $scope.model_customization.is_default;

                })
                .error(function (data) {
                    console.log(data);
                });
        };

        /* submit data */
        $scope.submit_customization = function(model_customization_form) {

            $scope.server_errors["model_customization"] = {};

            var old_customization_name = customization_name;
            var data = $scope.model_customization;

            if (customization_id) {
                var request_method = "PUT";
            }
            else {
                var request_method = "POST";
            }

            $http({
                method: request_method,
                /* this line is NOT needed; I'm not simulating form data, I'm passing pure JSON */
                /*headers: {'Content-Type': 'application/x-www-form-urlencoded'},*/
                url: $scope.api_url,
                data: data
            }).success(function (data) {

                /* I have to explicitly re-set 'id' & 'name' based on data b/c 'id' is not bound to an ng form element */
                customization_id = data.id;
                customization_name = data.name;
                $scope.is_default_model_customization = $scope.model_customization.is_default;

                if (old_customization_name != customization_name) {
                    $scope.set_urls();

                    //$location.path($scope.view_url);
                    //$location.replace($scope.view_url);

                    window.location = $scope.view_url;
                    /* TODO: I SHOULD UPDATE THE LOCATION "PROPERLY" */
                    /* TODO: W/ "$scope.apply($location.path($scope.view_url))" */
                    /* TODO: BUT THAT REQUIRES SETTING UP ROUTES */
                    // $scope.load();
                }
                else {
                    /* if I load a new page as a result of submission, */
                    /* then the Django messaging framework will have a msg waiting for me */
                    /* otherwise, display a standard "success" msg here */
                    show_msg("Successfully saved customization", "success");
                }

            }).error(function (data) {
                /* just in case this is an unexpected server error, log the content */
                console.log(data);
                /* but if I'm in this loop, I'm really expecting a (handled) validation error */

                $.each(data, function(field, errors) {
                    console.log("field="+field);
                    console.log("errors="+errors);
                    model_customization_form[field].$setValidity('server', false);
                    model_customization_form[field].$setDirty();
                    $scope.server_errors.model_customization[field] = errors.join(", ");
                });

                show_msg("Error saving customization", "error");
            });
        };

        $scope.set_urls();
        $scope.load();

        $scope.print_stuff = function() {
            console.log("session_key=" + session_key);
            console.log($scope.model_customization);
        };

    }]);

})();
