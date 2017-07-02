/* q_ng_edit.js */
/* ng app for dealing w/ QRealizations */

(function() {
    var app = angular.module("q_edit", ["q_base", "ngCookies", "ui.bootstrap", "djng.forms"]);

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

    /**************/
    /* DIRECTIVES */
    /**************/


    app.directive("tree", ["$global_services", function($global_services) {
        return {
            restrict: "EA",
            replace: false,
            scope: {
                model: "=",
                showCompletion: "=",
                depth: '=?'
            },
            templateUrl: "/static/questionnaire/templates/q_ng_tree.html",
            link: function($scope, $element, $attrs) {
                $scope.depth = angular.isDefined($scope.depth) ? parseInt($scope.depth) : 0;
                $scope.get_depth_as_array = function() {
                    var depth_array = new Array();
                    for (var i=0; i<$scope.depth; i++) {
                        depth_array.push(1);
                    }
                    return depth_array;
                }
                $scope.select_model = function(model) {
                    if (! model.display_detail) {
                        /* if this is the 1st time we are selecting the model, then set display detail to 'true' */
                        /* this will have the effect of activating the load-on-demand paradigm */
                        model.display_detail = true;
                    }
                    var root_model = $global_services.getData();
                    $scope.select_model_aux(root_model, model)
                }
                $scope.select_model_aux = function(current_model, model_to_select) {
                    current_model.is_selected = current_model.key == model_to_select.key
                    $.each(current_model.properties, function(i, property) {
                        if (property.is_hierarchical) {
                            $.each(property.relationship_values, function(j, target) {
                                $scope.select_model_aux(target, model_to_select);
                            });
                        }
                    });
                }
                $scope.activate_model = function(model) {
                    $scope.activate_model_aux(model, model.is_active)
                }
                $scope.activate_model_aux = function(model, activation) {
                    model.is_active = activation
                    $.each(model.properties, function(i, property) {
                        if (property.is_hierarchical) {
                            $.each(property.relationship_values, function(j, target) {
                                $scope.activate_model_aux(target, activation);
                            });
                        }
                    });
                }
            }
        }
    }]);

    app.directive("hierarchy", ["$global_services", function($global_services) {
        return {
            restrict: "EA",
            replace: false,
            scope: false,  /* don't create an isolate scope, just inherit the scope of the parent controller */
            templateUrl: "/static/questionnaire/templates/q_ng_hierarchy.html"
        }
    }]);

    app.directive("reference", ['$http', '$compile', '$global_services', function($http, $compile, $global_services) {

        return {
            restrict: 'E',
            replace: true,
            scope: {
                referenceType: '=',
                referenceIndex: '=',
                referenceDisabled: '=',
                referenceRemoveFunction: '&'
            },
            templateUrl: "/static/questionnaire/templates/q_ng_reference.html",
            link: function ($scope, $element, $attrs) {
                /* b/c the Q is so asynchronous, I need to wait to set "current_model" until the parent controller has loaded */
                $scope.loaded_property = false;
                $scope.$watch(function () {
                        return $scope.$parent.is_loaded;
                    },
                    function(is_loaded) {
                        if (is_loaded && !$scope.loaded_property) {
                            $scope.current_model = $scope.$parent.current_model;
                            $scope.loaded_property = true;
                        }
                    }
                );

                $scope.is_active = true;
                $scope.is_disabled = $scope.referenceDisabled;
                $scope.toggle_active = function() {
                    var dialog_title = "Are you sure you want to do this?  You will lose the currently defined reference.";
                    bootbox.confirm(dialog_title, function(result) {
                        if (result) {
                            $scope.$apply($scope.reset_reference());
                        }
                        else {
                            $scope.$apply($scope.is_active = ! $scope.is_active);
                        }
                    });

                };

                $scope.possible_references = [];
                $scope.get_possible_references = function() {
                   $global_services.setBlocking(true);

                   var url = "http://api.es-doc.org/2/summary/search?document_version=latest";
//                   url += "&document_type=" + $scope.referenceType;
                   url += "&document_type=" + $scope.current_model['relationship_references'][$scope.referenceIndex][9];
                   url += "&project=" + project_name;
                   console.log("trying to goto: " + url);
                   var proxy_url = "/services/proxy/"
                   var proxy_data = "response_format=" + "json" + "&url=" + encodeURIComponent(url);

                   $http({
                        method: "POST",
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        url: proxy_url,
                        data: proxy_data
                   })
                   .success(function(result) {

                        $scope.possible_references = result.results;
                        $scope.total_references = $scope.possible_references.length;
                        $scope.selected_reference = [];

                        $scope.possible_institutes = $.unique($.map($scope.possible_references, function(reference, index) {
                            return reference[1];
                        }));
                        $scope.total_institutes = $scope.possible_institutes.length;
                        $scope.selected_institute = null;

                        /* TODO: THIS BIT ONWARDS OUGHT TO BE MOVED INTO THE CONTROLLER */
                        $scope.paging_size = 12;
                        $scope.page_size = 4;
                        $scope.current_page = 1;

                        $scope.$watch("current_page", function() {
                            $scope.page_start = ($scope.current_page - 1) * $scope.paging_size;
                            $scope.page_end = $scope.current_page * $scope.paging_size;
                            $scope.paged_references = $scope.possible_references.slice($scope.page_start, $scope.page_end);
                            if ($scope.total_references == 0) {
                                $scope.page_start = -1;
                            }
                            if ($scope.page_end > $scope.total_references) {
                                $scope.page_end = $scope.total_references;
                            }
                        });

                        $scope.toggle_selected_reference = function(reference) {
                            if ($scope.selected_reference == reference) {
                                $scope.selected_reference = null;
                            }
                            else {
                                $scope.selected_reference = reference;
                            }
                        };

                        var dialog_title = "Please select a published document to reference";
                        var dialog_content = "" +
                            "<div>" +
                            "   <span><strong>selected document:&nbsp;</strong></span>" +
                            "   <input class='form-control' ng-model='selected_reference[4]' placeholder='please select a reference from the list below' type='text' readonly='true'/>" +
                            "</div>" +
                            "<hr/>" +
                            "<table style='width: 100%;'>" +
                            "   <!-- tables w/ explicit css are icky, but sometimes they are needed -->" +
                            "   <tr>" +
                            "       <td style='width: 50%;'>" +
//                            "           <div class='input-group'>" +
//                            "               <span class='input-group-addon'>filter by institute:&nbsp;</span>" +
//                            "               <select class='form-control' style='display: table-cell; width: 50%;' placeholder='foobar' ng-model='selected_institute' ng-options='institute for institute in possible_institutes'>" +
//                            "                   <option value='' selected>*</option>" +
//                            "               </select>" +
//                            "           </div>" +
                            "       </td>" +
                            "       <td class='small text-right' style='width: 50%;'>" +
                            "           <ul style='margin-bottom: 2px;' uib-pagination class='pagination pagination-sm' ng-model='current_page' total-items='total_references' max-size='page_size' items-per-page='paging_size' boundary-links='true' force-ellipses='true' previous-text='&lsaquo;' next-text='&rsaquo;' first-text='&laquo;' last-text='&raquo;'></ul>" +
                            "           <div><em>showing items {{ page_start + 1 }} to {{ page_end }} of {{ total_references }}</em></div>" +
                            "       </td>" +
                            "   </tr>" +
                            "</table>" +
                            "<div class='list-group'>" +
                            "   <a class='list-group-item' ng-repeat='reference in paged_references' ng-click='toggle_selected_reference(reference)' ng-class='{active: reference==selected_reference}'>" +
                            "       <span>{{ reference[4] }}</span>" +
                            "       <span class='documentation'>{{ reference[2] }}</span>" +
                            "   </a>"+
                            "   <div class='list-group-item' ng-show='total_references==0'>" +
                            "       <span class='documentation'>no referenceable documents found.</span>" +
                            "   </div>" +
                            "</div>";
                        var compiled_dialog_content = $compile(dialog_content)($scope)
                        bootbox.dialog({
                            message: compiled_dialog_content,
                            title: dialog_title,
                            buttons: {
                                cancel: {
                                    label: "Cancel",
                                    className: "btn-default",
                                    callback: function () {
                                        show_lil_msg("Maybe next time.");
                                    }
                                },
                                ok: {
                                    label: "OK",
                                    className: "btn-primary",
                                    callback: function () {
                                        $scope.$apply(function() {
                                            $scope.current_model["relationship_references"][$scope.referenceIndex] = $scope.selected_reference;
                                            /* I have to manually add "document_type" b/c it not returned by the ES-DOC-API */
                                            /* I AM HERE */
                                            $scope.current_model["relationship_references"][$scope.referenceIndex].push($scope.referenceType);
                                        });
                                    }
                                }
                            }
                        });
                   })
                   .error(function(error) {
                        show_msg("Error connecting to ES-DOC Archive", "error");
                        console.log(error);
                   }).finally(function() {
                        $global_services.setBlocking(false);
                   });
                };

                $scope.reset_reference = function() {
                    $scope.selected_reference = null;
                    $scope.current_model["relationship_references"][$scope.referenceIndex] = [
                        null, null, null, null, null, null, null, null, null, null
                    ];
                }


                $scope.remove_reference = function() {
                    $scope.referenceRemoveFunction({index: $scope.referenceIndex});

//                    var dialog_title = 'Are you sure you want to remove this reference?  <em>You cannot undo this operation.</em>';
//                    bootbox.confirm(dialog_title, function(result) {
//                        if (result) {
//                            $scope.$apply(function() {
//                                $scope.referenceRemoveFunction({index: $scope.referenceIndex});
//                            });
//                        }
//                        else {
//                           show_lil_msg("That's a good idea.");
//                        }
//                    });
                };

                $scope.change_reference = function() {
                    alert("change_reference");
                };
            }
        }
    }]);

    /***************/
    /* CONTROLLERS */
    /***************/

    /************************/
    /* top level controller */
    /************************/

    app.controller("EditorController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        /* $scope.server_errors['form_name']['field_name'] is used to store server errors */
        /* the placeholder for this info is created in QForm.add_custom_errors() line #224 */
        /* and that gets populated as needed in $scope.submit_realization below */
        $scope.server_errors = {};

        $scope.form_validity = true;

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        /* setup the urls to use for AJAX */
        /* this can be called multiple times as a fn */
        /* in case the id or name changes (after saving) */
        $scope.reset_urls = function() {
            $scope.api_url = api_url_dirname + "/";
            $scope.view_url = view_url_dirname + "/";
            if (realization_id) {
                $scope.api_url = $scope.api_url + realization_id + "/";
                $scope.view_url = $scope.view_url + realization_id + "/";
            }
        };
        $scope.reset_urls();

        /* now load initial JSON data (using the above urls) */
        if (realization_id) {
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
        /* that's okay; the reset of the code including all the other controllers use a watch on $global_services.isLoaded() before loading local variables */

        $scope.is_loaded = false;
        $scope.$watch(function() { return $global_services.isLoaded() },
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    var top_level_model = $global_services.getData();
                    /* set the top-level-model to be displayed */
                    /* (other models will be displayed via interaction w/ the GUI) */
                    top_level_model.display_detail = true;
                    top_level_model.is_selected = true;
                    $scope.is_loaded = true;
                }
            }
        );

        $scope.type = "EDITOR";

        $scope.show_completion = false;
        $scope.toggle_completion = function() {
            $scope.show_completion = !$scope.show_completion;
        }

        $scope.submit_realization = function() {
            /* TODO: UNLIKE THE CUSTOMIZER, THIS DOES NOT RENDER SERVER ERRORS */
            /* TODO: B/C I CAN'T REALLY WORK OUT WHICH FORM(S) TO RENDER THEM ON W/OUT A WHOLE LOT OF WORK */
            $global_services.setBlocking(true);

            var model = $global_services.getData();
            var old_realization_id = realization_id;

            if (realization_id) {
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
                /* I have to explicitly re-set a few things based on data */
                realization_id = data.id;
                realization_version = data.version;
                var model = $global_services.getModelFromPath("_DATA");
                model.id = realization_id;
                model.version = realization_version;
                if (old_realization_id != realization_id) {
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
                    /* TODO: SEE ABOVE COMMENT ABOUT NOT RENDERING ERRORS */
                });
                show_msg("Error saving realization", "error");
            })
            .finally(function() {
                $global_services.setBlocking(false);
            });
        };

        $scope.print_stuff = function() {
            /* print the current state of stuff */
            var model = $global_services.getModelFromPath("_DATA");
            console.log("session_key=" + session_key);
            console.log(model);

            $global_services.setBlocking(true);
            var url = "/services/log/";
            var data = "msg=" + JSON.stringify(model);
            $http({
                method: "POST",
                url: url,
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                data: data
            })
            .finally(function() {
                $global_services.setBlocking(false);
            });

        };

    }]);

    /*******************************/
    /* controller for a (sub)model */
    /*******************************/

    app.controller("ModelEditorController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        /* clear any parent scope */
        /* (as per http://stackoverflow.com/a/23225510/1060339) */
        /* Angular always checks parent scope to see if there is a variable w/ the same name ("prototypical inheritance") */
        /* b/c of the highly recursive nature of the Q, there will almost always be parent scope variables w/ the same name */
        /* but I want to keep these all separate (among other things, it lets me simplify forms' "scope_prefix" in "forms_edit_properties.QPropertyRealizationFormSet#add_default_form_arguments")
        /* hooray!!! */
        $scope.current_model = {};

        /* TODO: DO I NEED TO ADD THE ABOVE LINE TO SIMILAR PLACES IN "q_ng_customizer.js" ? */
        /* TODO: Angular docs recommend something a bit more complex: https://docs.angularjs.org/guide/directive#isolating-the-scope-of-a-directive */

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(function() { return $global_services.isLoaded() },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    $scope.current_model_path = $attrs.currentModelPath;
                    $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                    $scope.update_model_completion();
                    $scope.is_loaded = true;
                }
            }
        );

        $scope.type = "MODEL";

        $scope.$watch('current_model.is_complete', function(new_is_complete, old_is_complete) {
            if (new_is_complete != old_is_complete) {
                /* whenever completion changes, propagate that change to the parent property */
                var parent_property_controller = $scope.$parent;
                if (parent_property_controller.type == "PROPERTY") {
                    parent_property_controller.update_property_completion();
                }
                else {
                    console.log("could not find property_controller");
                }
            }
        });

        $scope.update_model_completion = function() {
            /* computes a model's completion based on its properties' completion */
            var properties_completion = $scope.current_model['properties'].reduce(function(value, property) {
                /* using 'reduce' above instead of 'map' in order to exclude meta properties */
                if (! property.is_meta) {
                    value.push(property.is_complete)
                }
                return value;
            }, [])
            var is_complete = properties_completion.every(function(is_complete) {
                return is_complete;
            });
            $scope.current_model['is_complete'] = is_complete;
        };

        /* TODO: THIS CODE IS REPEATED IN BOTH CONTROLLERS; I SHOULD MOVE IT TO A SINGLE PLACE ($global_services?) */
        $scope.init_value = function(key, value) {
            /* this is important; I have to add a watch to this function */
            /* b/c otherwise it would be called immediately before the above loading has taken place */
            /* in that case, "$scope.current_model" could still be bound to the parent's model */
            /* and all sorts of trouble & hilarity might ensue */
            $scope.$watch("is_loaded", function(is_loaded) {
                var initialized_key = "initialized_" + key;
                if (is_loaded && typeof $scope[initialized_key] == "undefined") {
                    $scope.current_model[key] = value;
                    $scope[initialized_key] = true;
               }
            });
        };

       /* some useful helper fns */

        $scope.get_models_by_attrs = function(models, attrs) {
            return $filter('filter')(
                models, attrs
            )
        };

        $scope.get_model_by_attrs = function(models, attrs) {
            var model = $filter('filter')(
                models, attrs
            )[0];
            return model;
        };

        $scope.get_model_by_index = function(models, index) {
            return models[index];
        };


    }]);

    /*****************************/
    /* controller for a category */
    /*****************************/

    app.controller("CategoryEditorController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        /* clear any parent scope */
        /* (as per http://stackoverflow.com/a/23225510/1060339) */
        /* Angular always checks parent scope to see if there is a variable w/ the same name ("prototypical inheritance") */
        /* b/c of the highly recursive nature of the Q, there will almost always be parent scope variables w/ the same name */
        /* but I want to keep these all separate (among other things, it lets me simplify forms' "scope_prefix" in "forms_edit_properties.QPropertyRealizationFormSet#add_default_form_arguments")
        /* hooray!!! */
        this.current_model = {};

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(function() { return $global_services.isLoaded() },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    $scope.current_model_path = $attrs.currentModelPath;
                    $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                    $scope.update_category_completion();
                    $scope.is_loaded = true;
                }
            }
        );

        $scope.type = "CATEGORY";

        $scope.get_properties = function() {
            var properties_keys = $scope.current_model["properties_keys"];
            var model_properties = $scope.$parent.current_model["properties"];
            var category_properties = model_properties.reduce(function(value, mp) {
                if (properties_keys.indexOf(mp.key) >= 0) {
                    value.push(mp);
                }
                return value;
            }, []);
            return category_properties;
        };

        $scope.update_category_completion = function() {
            /* computes a category's completion based on its properties' completion */
            var properties_completion = $scope.get_properties().reduce(function(value, property) {
                /* using 'reduce' above instead of 'map' in order to exclude meta properties */
                if (! property.is_meta) {
                    value.push(property.is_complete)
                }
                return value;
            }, [])
            var is_complete = properties_completion.every(function(is_complete) {
                return is_complete;
            });
            $scope.current_model["is_complete"] = is_complete;
        };

        /* some useful fns */
        $scope.get_models_by_attrs = function(models, attrs) {
            return $filter('filter')(
                models, attrs
            )
        };

        $scope.get_model_by_attrs = function(models, attrs) {
            var model = $filter('filter')(
                models, attrs
            )[0];
            return model;
        };

    }]);

    /*****************************/
    /* controller for a property */
    /*****************************/

    app.controller("PropertyEditorController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        /* clear any parent scope */
        /* (as per http://stackoverflow.com/a/23225510/1060339) */
        /* Angular always checks parent scope to see if there is a variable w/ the same name ("prototypical inheritance") */
        /* b/c of the highly recursive nature of the Q, there will almost always be parent scope variables w/ the same name */
        /* but I want to keep these all separate (among other things, it lets me simplify forms' "scope_prefix" in "forms_edit_properties.QPropertyRealizationFormSet#add_default_form_arguments")
        /* hooray!!! */
        $scope.current_model = {};

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(function() { return $global_services.isLoaded() },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    $scope.current_model_path = $attrs.currentModelPath;
                    $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                    $scope.is_loaded = true;
                }
            }
        );

        /* yes, confusingly, the above code has just set "current_model" to be a specific property */
        /* (it uses "model" in the Django sense of the word and "property" in the CIM sense of the word) */

        $scope.type = "PROPERTY";

        $scope.$watch('current_model.is_complete', function(new_is_complete, old_is_complete) {
            if (new_is_complete != old_is_complete) {
                /* whenever completion changes, propagate that change to the parent category/model */
                var parent_category_controller = $scope.$parent;
                if (parent_category_controller.type == "CATEGORY") {
                    parent_category_controller.update_category_completion();
                }
                else {
                    console.log("could not find category_controller");
                }
                var parent_model_controller = parent_category_controller.$parent;
                if (parent_model_controller.type == "MODEL") {
                    parent_model_controller.update_model_completion();
                }
                else {
                    console.log("could not find model_controller");
                }
            }
        });

        $scope.update_property_completion = function() {

//            if ($scope.current_model["cardinality_min"] != "0") {
            if ($scope.current_model["customization"]["is_required"])  {
                if ($scope.current_model["is_nil"]) {
                    /* something that is required but explicitly set to "nil" is still considered complete */
                    $scope.current_model['is_complete'] = true;
                }
                else {
                    var field_type = $scope.current_model['field_type'];
                    if (field_type == "ATOMIC") {
                        if ($scope.current_model["atomic_value"]) {
                            $scope.current_model["is_complete"] = true;
                        }
                        else {
                            $scope.current_model["is_complete"] = false;
                        }
                    }
                    else if (field_type == "ENUMERATION") {
                        var enumeration_value = $scope.current_model["enumeration_value"];


                        if (enumeration_value.length) {
                            if (enumeration_value.indexOf(ENUMERATION_OTHER_CHOICE) >= 0) {
                                var enumeration_other_value = $scope.current_model["enumeration_other_value"];
                                if (enumeration_other_value) {
                                    $scope.current_model["is_complete"] = true;
                                }
                                else {
                                    $scope.current_model["is_complete"] = false;
                                }
                            }
                            else {
                                $scope.current_model["is_complete"] = true;
                            }
                        }
                        else {
                            $scope.current_model["is_complete"] = false;
                        }
                    }
                    else { /* field_type == "RELATIONSHIP" */
                        if ($scope.current_model["use_references"]) {
                            var relationship_references = $scope.current_model["relationship_references"];
                            if (relationship_references.length >= $scope.current_model["cardinality_min"]) {
                                $scope.current_model["is_complete"] = true;
                            }
                            else {
                                $scope.current_model["is_complete"] = false;
                            }
                        }
                        else if ($scope.current_model["use_subforms"]) {
                            var relationship_values = $scope.current_model["relationship_values"]
                            if (relationship_values.length >= $scope.current_model["cardinality_min"]) {
                                $scope.current_model["is_complete"] = true;
                            }
                            else {
                                $scope.current_model["is_complete"] = false;
                            }
                        }
                    }
                }
            }
            else {
                $scope.current_model["is_complete"] = true;
            }
        };

        $scope.$watch('current_model.is_nil', function(new_is_nil, old_is_nil) {
            if ((new_is_nil != old_is_nil) && $scope.current_model["cardinality_min"] != "0") {
                console.log("about to call update_property_completion()");
                $scope.update_property_completion();
            }
        });

        /* TODO: THIS CODE IS REPEATED IN BOTH CONTROLLERS; I SHOULD MOVE IT TO A SINGLE PLACE ($global_services?) */
        $scope.init_value = function(key, value) {
            /* this is important; I have to add a watch to this function */
            /* b/c otherwise it would be called immediately before the above loading has taken place */
            /* in that case, "$scope.current_model" could still be bound to the parent's model */
            /* and all sorts of trouble & hilarity might ensue */
            $scope.$watch("is_loaded", function(is_loaded) {
                var initialized_key = "initialized_" + key;
                if (is_loaded && typeof $scope[initialized_key] == "undefined") {
                    $scope.current_model[key] = value;
                    $scope[initialized_key] = true;
               }
            });
        };

        var relationship_reference_field_name = "relationship_references";
        var relationship_subform_field_name = "relationship_values";

        $scope.add_relationship_reference = function() {
            if ($scope.current_model.possible_relationship_target_types.length == 1) {
                var reference_type = $scope.current_model.possible_relationship_target_types[0].type;
                $scope.current_model[relationship_reference_field_name].push(
                    [null, null, null, null, null, null, null, null, null, reference_type]
                );
            }
            else {
                var dialog_title = "Please select the type of document you wish to reference:";
                var dialog_options = $.map($scope.current_model.possible_relationship_target_types, function (target, index) {
                    return {
                        text: target.name,
                        value: target.type
                    }
                });
                dialog_options.unshift({
                    text: "<span style='color: red;'>Please select an option...</span>",
                    value: ""
                });
                bootbox.prompt({
                    title: dialog_title,
                    inputType: "select",
                    placeholder: 'my placeholder',
                    inputOptions: dialog_options,
                    callback: function(reference_type) {
                        if (reference_type) {
                            $scope.$apply(function() {
                                $scope.current_model[relationship_reference_field_name].push(
                                    [null, null, null, null, null, null, null, null, null, reference_type]
                                );
                            });
                        }
                    }
                });
            }
        };

        $scope.remove_relationship_reference = function(index) {
            var dialog_title = 'Are you sure you want to remove this reference?  <em>You cannot undo this operation.</em>';
            bootbox.confirm(dialog_title, function(result) {
                if (result) {
                    $scope.$apply(function() {
                        $scope.current_model[relationship_reference_field_name].splice(index, 1)
                    });
                }
                else {
                   show_lil_msg("That's a good idea.");
                }
            });

        };

        $scope.add_relationship_value = function(property_title) {
            /* this fn just gets the id of the target_proxy to use when adding */
            /* and then passes that to "add_relationship_value_aux" below */
            if ($scope.current_model.possible_relationship_target_types.length == 1) {
                var target_proxy_id = $scope.current_model.possible_relationship_target_types[0].pk;
                $scope.add_relationship_value_aux(target_proxy_id);
            }
            else {
                var dialog_title = '<span>Select the type of <b>' + property_title + '</b> to add</span>';
                /* rather than using ng-repeat functionality to create these inputs, I manually loop through all targets */
                /* to do it any other way would require loads of coding and turning this into a directive - which just seems like overkill */
                var dialog_options = $.map($scope.current_model.possible_relationship_target_types, function (target, index) {
                    var option_value = target.pk;
                    var option_name = target.name;
                    var option = '' +
                        '<label for="option_' + option_value + '">' +
                        '   <input id="option_' + option_value + '" name="target" type="radio" value="' + option_value + '"';
                    if (index == 0) {
                        option += ' checked ';  /* the 1st option is checked by default */
                    }
                    option += '>' +
                        '       &nbsp;' + option_name +
                        '</label>';
                    return option;
                });
                var dialog_content = dialog_options.join("<br/>");
                bootbox.dialog({
                    message: dialog_content,
                    title: dialog_title,
                    buttons: {
                        cancel: {
                            label: "Cancel",
                            className: "btn-default",
                            callback: function () {
                                show_lil_msg("Maybe next time.");
                            }
                        },
                        ok: {
                            label: "OK",
                            className: "btn-primary",
                            callback: function () {
                                var target_proxy_id = $("input[name='target']:checked").val();
                                $scope.add_relationship_value_aux(target_proxy_id);
                            }
                        }
                    }
                });
            }
        };

        $scope.add_relationship_value_aux = function(target_proxy_id) {
            $global_services.setBlocking(true);
            var url = "/services/realization_add_relationship_value/";
            var data = "session_key=" + session_key + "&target_proxy_id=" + target_proxy_id + "&key=" + $scope.current_model.key;
            $http({
                method: "POST",
                url: url,
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                data: data
            })
            .then(
                function(result) {
                    /* success */
                    $scope.current_model[relationship_subform_field_name].push(result.data);
                    $global_services.setBlocking(false);
                },
                function(error) {
                    /* error */
                    console.log(error.data);
                    $global_services.setBlocking(false);
                }
           )
        };

        $scope.remove_relationship_value = function(property_title, target_key, target_index) {
            var dialog_title = 'Are you sure you want to remove this <b>' + property_title + '</b> and all of its content?<br/><em>You cannot undo this operation.</em>';
            bootbox.confirm(dialog_title, function(result) {
                if (result) {
                    $scope.current_model[relationship_subform_field_name].splice(target_index, 1);
                    $scope.remove_relationship_value_aux(target_key, target_index);
                }
                else {
                   show_lil_msg("That's a good idea.");
                }
            });
        };

        $scope.remove_relationship_value_aux = function(target_key, target_index) {
            /* this removes the model from the server cache */
            /* strictly speaking, this isn't needed b/c the client JSON object will replace the server cache upon saving, */
            /* but this fn also forces the code to "do something" which provides a loading bar and refreshes the display */
            /* and, anyway, it's good housekeeping to always keep the server cache in sync w/ the client object */
            $global_services.setBlocking(true);
            var url = "/services/realization_remove_relationship_value/";
            var data = "session_key=" + session_key + "&target_index=" + target_index + "&target_key=" + target_key + "&key=" + $scope.current_model.key;
            $http({
                method: "POST",
                url: url,
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                data: data
            }).then(
                function(result) {
                    /* success */
                    $global_services.setBlocking(false);
                },
                function(error) {
                    /* error */
                    console.log(error.data);
                    $global_services.setBlocking(false);
                }
           )
        };



        $scope.$watchCollection("current_model.relationship_references", function(new_references, old_references) {
            if (new_references.length != old_references.length) {
                $scope.update_property_completion();
            }
        });

// don't need an explicit watch on subform relationships, b/c altering the completion of the target models forces updating the completion of the parent property
// (unlike the situation w/ references, above)...
//        $scope.$watchCollection("current_model.relationship_values", function(new_relationships, old_relationships) {
//            if (new_relationships.length != old_relationships.length) {
//                var parent_property_controller = $scope.$parent;
//                if (parent_property_controller.type == "PROPERTY") {
//                    parent_property_controller.update_property_completion();
//                }
//                else {
//                    console.log("could not find property_controller");
//                }
//            }
//        });

//        also don't need this, b/c "update_property_completion()" is called from the enumeration directive
//        (although, using this "watch" is probably more intuitive... TODO: LOOK INTO USING THIS CODE)
//        $scope.$watchCollection("current_model.enumeration_value", function(old_enumeration_value, new_enumeration_value) {
//            if (old_enumeration_value != new_enumeration_value) {
//                console.log("you changed an enumeration");
//            }
//        });

        /* TODO: I DON'T LIKE DEFINING THIS FN HERE; IT OUGHT TO HAVE GLOBAL SCOPE */
        /* TODO: OR, BETTER YET, BE PART OF THE <enumeration> DIRECTIVE ITSELF */
        $scope.value_in_array = function(value, array) {
            return $.inArray(value, array) >= 0;
        };

    }]);

    /***********/
    /* THE END */
    /***********/

})();