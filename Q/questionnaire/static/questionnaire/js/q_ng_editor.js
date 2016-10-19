/* q_ng_editor.js */
/* ng app for dealing w/ QRealizations */

(function() {
    var app = angular.module("q_editor", ["q_base", "ngCookies", "ui.bootstrap", "ui.bootstrap.datetimepicker", "ng.django.forms"]);

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

    app.controller("EditorController", ['$scope', '$global_services', '$attrs', '$http', '$cookies', '$location', '$filter', function($scope, $global_services, $attrs, $http, $cookies, $location, $filter) {

        $scope.blocking = function() {
            return $global_services.getBlocking();
        };

        $scope.show_completion_status = false;

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
            if (realization_id) {
                $scope.api_url = $scope.api_url + realization_id + "/";
                $scope.view_url = $scope.view_url + realization_id + "/";
            }
        };
        $scope.reset_urls();

        /* now load initial JSON data (using the above urls) */
        if (realization_id) {
            /* if this is an existing realization, the url will be normal */
            $global_services.load($scope.api_url);
        }
        else {
            /* if this is a new realization, the url will need to be changed to get the already cached serialization */
            $global_services.load(
                $scope.api_url + "cache/?session_key=" + session_key
            )
        }
        /* those were asynchronous calls */
        /* that's okay; the other controllers use a watch on $global_services.isLoaded() before loading their local variables */

        $scope.is_read_only = function() {
            return read_only;
        };

        $scope.submit_realization = function() {
            $global_services.setBlocking(true);
            var model = $global_services.getData();
            var old_realization_id = realization_id;

            if (realization_id) {
                /* updating an existing realization */
                var request_method = "PUT";
            }
            else {
                /* creating a new realization */
                var request_method = "POST";
            }

            $http({
                method: request_method,
                /* this line is NOT needed; I'm not simulating form data, I'm passing pure JSON */
                /*headers: {'Content-Type': 'application/x-www-form-urlencoded'},*/
                url: $scope.api_url,
                data: model
            })
            .success(function (data) {
                /* I have to explicitly re-set 'id' based on data b/c 'id' is not bound to an ng form element */
                realization_id = data.id;
                if (old_realization_id != realization_id) {
                    $scope.reset_urls();
                    window.location = $scope.view_url;
                    /* TODO: I SHOULD UPDATE THE LOCATION "PROPERLY" */
                    /* TODO: W/ "$scope.apply($location.path($scope.view_url))" */
                    /* TODO: BUT THAT REQUIRES SETTING UP ROUTES */
                }
                else {
                    /* the above branch automatically gets a pending msg by virtue of the new page load */
                    /* in this branch, I have to manually check for a pending msg b/c I don't reload the page */
                    check_msg();

                }
            })
            .error(function (data) {
                /* just in case this is an unexpected server error, log the content */
                console.log(data);

                /* I AM HERE */
                /* TODO: DEAL W/ SERVER ERRORS IN DATA; MAP TO FORMS */
                /* TODO: I KNOW THAT THE ONLY SERVER ERRORS CAN BE ON THE PARENT FORM, CUSTOMIZATION SECTION */
                /* TODO: (THEY ARE INVALID "name" & INVALID "is_default") */
                /* TODO: HOWEVER, I'LL STILL HAVE TO SOLVE THE GENERAL CASE FOR THE EDITING FORMS */

                show_msg("Error saving document", "error");
            })
            .finally(function() {
                $global_services.setBlocking(true);
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

        /* check the arguments */
        if (!$attrs.currentModelPath == !$attrs.currentModel) {
            /* '(!x == !x)' simulates XOR; one and only one attr is required */
            throw new Error("ModelRealizationController needs either the current_model or the current_model_path")
        };

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(function () {
                return $global_services.isLoaded();
            },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    if ($attrs.currentModelPath) {
                        $scope.current_model_path = $attrs.currentModelPath;
                        $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                        /* HARD-CODING THIS; UNLIKE CUSTOMIZATIONS I WANT TO DISPLAY EVERYTHING (LOAD THE FORM) UPON CONTROLLER LOAD */
                        $scope.current_model.display_detail = true;
                    }
                    else if ($attrs.currentModel) {
                        throw new Error("ModelEditorController CANNOT SUPPORT 'current_model' ATTRIBUTE YET");
                        $scope.current_model = $attrs.currentModel;
                        $scope.current_model_path = $global_services.getPathFromModel($attrs.currentModel);
                        /* HARD-CODING THIS; UNLIKE CUSTOMIZATIONS I WANT TO DISPLAY EVERYTHING (LOAD THE FORM) UPON CONTROLLER LOAD */
                        $scope.current_model.display_detail = true;
                    }
                    $scope.is_loaded = true;
                }
            }
        );

        $scope.update_model_completion = function() {
            /* computes a model's completion based on its properties' completion */
            var properties_completion = $scope.current_model['properties'].map(function(property) {
                return property.is_complete;
            });
            $scope.current_model['is_complete'] = properties_completion.every(function(is_complete) {
                return is_complete;
            });
        };

        /* TODO: THIS CODE IS REPEATED IN BOTH CONTROLLERS; I SHOULD MOVE IT TO A SINGLE PLACE ($global_services?) */
        $scope.init_value = function(key, value) {
            /* this is important; I have to add a watch to this function */
            /* b/c otherwise it would be called immediately before the above loading has taken place */
            /* in that case, "$scope.current_model" could still be bound to the parent's model */
            /* and all sorts of trouble & hilarity would ensue */
            $scope.$watch("is_loaded", function(is_loaded) {
                var initialized_key = "initialized_" + key;
                if (is_loaded && typeof $scope[initialized_key] == "undefined") {
                    $scope.current_model[key] = value;
                    $scope[initialized_key] = true;
               }
            });
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

        /* check the arguments */
        if (!$attrs.currentModelPath == !$attrs.currentModel) {
            /* '(!x == !x)' simulates XOR; one and only one attr is required */
            throw new Error("ModelRealizationController needs either the current_model or the current_model_path")
        };

        /* load initial data */
        $scope.is_loaded = false;
        $scope.$watch(function () {
                return $global_services.isLoaded();
            },
            /* only load local stuff after $global_services has loaded stuff */
            function (is_loaded) {
                if (is_loaded && !$scope.is_loaded) {
                    if ($attrs.currentModelPath) {
                        $scope.current_model_path = $attrs.currentModelPath;
                        $scope.current_model = $global_services.getModelFromPath($attrs.currentModelPath);
                    }
                    else if ($attrs.currentModel) {
                        throw new Error("ModelEditorController CANNOT SUPPORT 'current_model' ATTRIBUTE YET");
                        $scope.current_model = $attrs.currentModel;
                        $scope.current_model_path = $global_services.getPathFromModel($attrs.currentModel);
                    }
                    $scope.is_loaded = true;

                    /* now that current_model is loaded, I can setup some other initial values */
                    $scope.cardinality_min = $scope.current_model.cardinality.split('|')[0];
                    $scope.cardinality_max = $scope.current_model.cardinality.split('|')[1];
                }
            }
        );
        $scope.isLoaded = function() {
            return $scope.is_loaded;
        };

        /* TODO: I DON'T LIKE DEFINING THIS FN HERE; IT OUGHT TO HAVE GLOBAL SCOPE */
        /* TODO: OR, BETTER YET, BE PART OF THE <enumeration> DIRECTIVE ITSELF */
        /* TODO: OR HAVE THE FN CALL IN "forms_edit_properties.QPropertyRealizationForm#customize" CONVERT THE INITIAL VALUE TO AN ARRAY */
        $scope.check_enumeration = function(arg, value) {
            /* checks if a particular value is in an enumeration */
            /* note that depending on when this fn is called `value` may not yet be an array */
            /* (it is serialized as a '|' deliminated string and only converted to a JS array through the <enumeration> directive) */
            if (value.constructor != Array) {
                value = value.split('|');
            }
            var arg_in_value = $.inArray(arg, value);
            return arg_in_value > 0;
        };

        /* yes, confusingly, the above code has just set "current_model" to be a specific property */
        /* (it uses "model" in the Django sense of the word and "property" in the CIM sense of the word) */

        $scope.get_current_model = function() {
            $scope.$watch("is_loaded", function(is_loaded) {
               if (is_loaded) {
                   return $scope.current_model;
               }
            });
        };

        /* deal w/ tracking completion */

        $scope.$watch('current_model.is_complete', function(new_is_complete, old_is_complete) {
            if (new_is_complete != old_is_complete) {
                /* whenever completion changes, propagate that change to the parent model */
                $scope.update_model_completion();
            }
        });

        $scope.update_property_completion = function() {
            var cardinality_min = $scope.cardinality_min;
            if (cardinality_min) {
                /* if ths property is required then check some things... */

                    if ($scope.current_model['is_nil']) {
                        /* something that is required but explicitly set to "nil" is still considered complete */
                        $scope.current_model['is_complete'] = true;
                    }
                    else {
                        var field_type = $scope.current_model['field_type'];
                        if (field_type == "ATOMIC") {
                            var atomic_value = $scope.current_model['atomic_value']
                            if (atomic_value) {
                                $scope.current_model['is_complete'] = true;
                            }
                            else {
                                $scope.current_model['is_complete'] = false;
                            }
                        }

                        else if (field_type == "ENUMERATION") {
                            var enumeration_value = $scope.current_model['enumeration_value']
                            if (enumeration_value.length ) {
                                if (enumeration_value.indexOf("_OTHER") != -1) {
                                    var enumeration_other_value = $scope.current_model['enumeration_other_value']
                                    if (enumeration_other_value) {
                                        $scope.current_model['is_complete'] = true;
                                    }
                                    else {
                                        $scope.current_model['is_complete'] = false;
                                    }
                                }
                                else {
                                    $scope.current_model['is_complete'] = true;
                                }
                            }
                            else {
                                $scope.current_model['is_complete'] = false
                            }

                        }


                    }

            }
            else {
                /* a non-required property is complete by default */
                /* TODO: DOES THIS TAKE INTO ACCOUNT CUSTOMIZATIONS ? */
                $scope.current_model['is_complete'] = true;
            }
        };

        /* deal w/ nillable properties */
        $scope.$watch('current_model.is_nil', function(new_is_nil, old_is_nil) {
            if ((new_is_nil != old_is_nil) && $scope.current_model['is_required']) {
                $scope.update_property_completion();
            }
        });

        /* deal w/ atomic properties */

        /* deal w/ enumeration properties */

        /* deal w/ relationship properties */

        var relationship_subform_field_name = "relationship_values";
        var relationship_reference_field_name = "relationship_references";

        $scope.is_multiple = function() {
            return ($scope.cardinality_max != '0' && $scope.cardinality_max != '1')
        };

        $scope.is_single = function() {
            return $scope.cardinality_max == '1'
        };

        $scope.add_relationship_value = function(property_title) {
            /* this just gets the id of the target_proxy to use when adding */
            /* and then passes that to "add_relationship_value_aux" below */
            if ($scope.current_model.possible_relationship_targets.length == 1) {
                var target_proxy_id = $scope.current_model.possible_relationship_targets[0].pk;
                $scope.add_relationship_value_aux(target_proxy_id);
            }
            else {
                var dialog_title = '<span>Select the type of <b>' + property_title + '</b> to add</span>';
                /* rather than using ng-repeat functionality to create these inputs, I manually loop through all targets */
                /* to do it any other way would require loads of coding and turning this into a directive - which just seems like overkill */
                var dialog_options = $.map($scope.current_model.possible_relationship_targets, function (target, index) {
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
            /* this does the actual adding */
            /* it gets called if "add_relationship_value" returns a valid target_proxy_id */
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
                    var new_relationship_value = result.data;
                    $scope.current_model[relationship_subform_field_name].push(new_relationship_value);
                    $global_services.setBlocking(false);
                },
                function(error) {
                    /* error */
                    console.log(error.data);
                    $global_services.setBlocking(false);
                }
           )
        };

        $scope.remove_relationship_value = function(property_title, target_index) {
            var dialog_title = 'Are you sure you want to remove this <b>' + property_title + '</b>?<br/><i>You cannot undo this operation.</i>';
            bootbox.confirm(dialog_title, function(result) {
                if (result) {
                    $scope.current_model[relationship_subform_field_name].splice(target_index, 1);
                    $scope.remove_relationship_value_aux(target_index);
                }
                else {
                   show_lil_msg("That's a good idea.");
                }
            });
        };

        $scope.remove_relationship_value_aux = function(target_index) {
            /* this removes the model from the server cache */
            /* strictly speaking, this isn't needed b/c the client JSON object will replace the server cache upon saving, */
            /* but this fn also forces the code to "do something" which provides a loading bar and refreshes the display */
            $global_services.setBlocking(true);
            var url = "/services/realization_remove_relationship_value/";
            var data = "session_key=" + session_key + "&target_index=" + target_index + "&key=" + $scope.current_model.key;
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

        /* deal w/ enumerations */

        /* TODO: MOVE THIS TO A BASE FILE */
        $scope.value_in_array = function(value, array) {
            //console.log("looking for: '" + value + "' in: " + array);
            return $.inArray(value, array) != -1;
        };

        /* deal w/ customizing properties */

        /* TODO: THIS CODE IS REPEATED IN BOTH CONTROLLERS; I SHOULD MOVE IT TO A SINGLE PLACE ($global_services?) */
        $scope.init_value = function(key, value) {
            /* this is important; I have to add a watch to this function */
            /* b/c otherwise it would be called immediately before the above loading has taken place */
            /* in that case, "$scope.current_model" could still be bound to the parent's model */
            /* and all sorts of trouble & hilarity would ensue */
            $scope.$watch("is_loaded", function(is_loaded) {
                var initialized_key = "initialized_" + key;
                if (is_loaded && typeof $scope[initialized_key] == "undefined") {
                    $scope.current_model[key] = value;
                    $scope[initialized_key] = true;
               }
            });
        };

    }]);


    /***********/
    /* THE END */
    /***********/

})();