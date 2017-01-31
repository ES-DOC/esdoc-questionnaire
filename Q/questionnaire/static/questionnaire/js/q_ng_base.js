/* q_base.js */

/* angular app for Questionnaire */
/* all page-specific apps inherit from this */

(function() {
    var app = angular.module("q_base", ["q_base", "ui.bootstrap", "angular-loading-bar"]);
    /* note my use of angular-loading-bar above */
    /* this intercepts every $http call and displays a tiny loading bar */
    /* (I have overwritten the CSS to make it bigger: see "q_bootstrap.less") */

    /***************/
    /* CONTROLLERS */
    /***************/

    app.controller("TabController", ['$scope', function($scope) {
        /* simple lil controller for tabs */
        /* (only used in the editor, where not all tabs are displayed at once) */
        this.selected_first_tab = false;
        this.selected_tab = null;
        this.select_tab = function(tab_id) {
            this.selected_tab = tab_id;
        };
        this.is_tab_selected = function(tab_id) {
            return this.selected_tab == tab_id;
        };
        this.select_first_tab = function(tab_id) {
            /* the first time I call this fn, select the corresponding tab */
            /* ignore all other times (there can be only one) */
            if (!this.selected_first_tab) {
                this.selected_tab = tab_id;
                this.selected_first_tab = true
            }
        };
    }]);

    app.controller("FieldsetController", function() {
        /* simple lil controller for collapsible fieldsets */
        var fieldset_controller = this;
        fieldset_controller.is_collapsed = false;
    });

    /*************/
    /* FACTORIES */
    /*************/

    app.factory('$global_services', ['$http', function($http) {

        /*****************************/
        /* global app-wide variables */
        /*****************************/

        var _blocking = false;

        var _is_loaded = false;

	    var _DATA =  {};  /* (top-level controller resets this) */

        var _NON_MODIFYING_SORTABLE_OPTIONS = {
            /* this is used as a base to build up other sortable_options */
            /* it includes some very COMPLEX but really CLEVER code which allows */
            /* the sorted items to have their "order" attribute changed */
            /* w/out actually changing their order in the JSON object */
            /* (this was required for the load-on-demand paradigm to work) */
            /* (b/c that binds ng-model to an indexed item in the JSON array) */
            /* TODO: NOW THAT I GET ITEMS VIA "key" AS OPPOSED TO "index" DO I STILL NEED THIS COMPLEXITY ? */
            containment: "parent",  /* prevent overflows */
            helper : 'clone',  /* this awesome lil hack prevents sorting from firing the click event */
            start: function (e, ui) {
                ui.placeholder.height(ui.item.height());
                ui.placeholder.width(ui.item.width());
            },
            update: function(e, ui) {
                /* THIS WAS HARD! */
                /* I MAKE AN ARRAY OF INDICES WHICH I RE-ORDER AS IF THAT WERE THE ARRAY BEING SORTED */
                /* I THEN UPDATE THE "order" ATTRIBUTE OF THE NG ARRAY BASED ON THAT RE-ORDERED INDEX ARRAY */
                var models = ui.item.sortable.sourceModel;
                var old_index = ui.item.sortable.index;
                var new_index = ui.item.sortable.dropindex;
                var sorted_model_indices = sort_objects_by_attr(
                    $.map(models, function(obj, i) {
                        /* TODO: I CAN PROBABLY SIMPLIFY THIS; I ONLY NEED "index" */
                        return {"index": i, "order": obj.order }
                    }),
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

        /**************/
        /* global fns */
        /**************/

        function get_model_from_path(path) {
            /* given a JSON "path" return model (part of _DATA) */
            var current_obj = _DATA;
            path = path.split('.');

            if (path[0] == "_DATA") {
              path.shift();
            }

            for (var i=0; i<path.length; i++) {

    	        var key = path[i];
                var is_array = key.match(/(.*)\[([0-9]+)\]/)
                if (is_array != null) {
      	            var key_name = is_array[1];
                    var key_number = is_array[2];
                    current_obj = current_obj[key_name][key_number];
                }
                else {
      	            var key_name = key;
                    /* not an array; no key_number */
                    current_obj = current_obj[key_name];
                }
            }

            return current_obj;
        };

        /***********************/
        /* services to provide */
        /***********************/

	    return {
            /* note: ng likes camelCase but I like under_scores */
            getModelFromPath: get_model_from_path,
            getSortableOptions: function() {
                return _NON_MODIFYING_SORTABLE_OPTIONS;
            },
            /* (re)load data */
            load: function(url) {
                /* I have to use promises b/c $http is asynchronous */
                /* that's probably for the best */
                /* (see http://stackoverflow.com/questions/12505760/processing-http-response-in-service) */
                var promise = $http.get(url, {format: "json"})
                    .success(function (data) {
                        _DATA = data;
                        _is_loaded = true;
                    })
                    .error(function (data) {
                        console.log(data);
                        _is_loaded = false;
                    });
                return promise;
            },
            /* work out if data has been loaded */
            isLoaded: function() {
                return _is_loaded;
            },
            /* work out if interaction should be blocked */
            getBlocking: function() {
                return _blocking;
            },
            /* toggle interaction */
            setBlocking: function(blocking) {
                _blocking = blocking;
            },
            /* get the entire model at once */
            getData: function() {
                return _DATA;
            }
        };

    }]);

    /**************/
    /* DIRECTIVES */
    /**************/

    /**************************/
    /* render some popup help */
    /**************************/

    app.directive('help', ['$compile', '$sce', function($compile, $sce) {
        return {
            restrict: 'E',
            replace: true,
            scope: {},
            template: "" +
                "<span class='help glyphicon glyphicon-info-sign'" +
                      "data-toggle='popover' data-trigger='focus' data-container='body'" +
                      "data-content='{{help_text}}'>" +
                "</span>",
            link: function(scope, element, attrs) {
                /* TODO: REMOVE ANY EMBEDDED QUOTES FROM helpText ATTRIBUTE */
                scope.help_text = $sce.trustAsHtml(attrs["helpText"]);
            }
        }
    }]);

    /***************************************************/
    /* track the validity of dynamically-created forms */
    /***************************************************/

    app.directive('watchFormValidity', function() {
        return {
            restrict: "A",
            link: function (scope, element, attrs) {
                /* note that ng converts everything to camelCase */
                var scope_variable = attrs["watchFormValidity"];
                var form_name = attrs["name"];
                var form_validity_expression = form_name + ".$valid";

                /* this is super-amazingly-cool; I am a javascript god! */
                /* I can bind the scope variable to ng-disabled on any button */
                scope.$watch(form_validity_expression, function (form_validity) {
                    scope[scope_variable] = form_validity;
                }, true);
            }
        }
    });

    /*********************************/
    /* make a pretty drop-down input */
    /*********************************/

    app.directive('enumeration', ['$sce', function($sce) {

        return {
            restrict: 'E',
            replace: true,
            scope: {
                enumerationChoices: "=",
                enumerationMultiple: "=",
                enumerationName: "=",
                enumerationFunction: "&"
            },
            templateUrl: "/static/questionnaire/templates/q_ng_enumeration.html",
            link: function ($scope, $element, $attrs) {
                /* b/c the Q is so asynchronous, I need to wait to set "current_model" until the parent controller has loaded */
                $scope.loaded_enumeration = false;
                $scope.$watch(function () {
                        return $scope.$parent.is_loaded;
                    },
                    function(is_loaded) {
                        if (is_loaded && !$scope.loaded_enumeration) {
                            $scope.current_model = $scope.$parent.current_model;
                            /* now set the initial values */
                            var initial_choices = $scope.current_model[$scope.enumerationName]
                            $.each($scope.enumerationChoices, function(i, choice) {
                                choice.is_active = initial_choices.indexOf(choice.value) >= 0;
                            });
                            /* also, initialize any custom widgets in the template _after_ content is loaded */
                            init_widgets(helps, $element.find(".help"));
                            $scope.loaded_enumeration = true;
                        }
                    }
                );
                $scope.is_open = false;
                $scope.TITLE_LIMIT = 2;
                if ($scope.enumerationMultiple) {
                    $scope.title_placeholder = "<span class='placeholder'>Please select option(s)</span>";
                }
                else {
                    $scope.title_placeholder = "<span class='placeholder'>Please select an option</span>";
                }
                $scope.get_enumeration_title = function () {
                    var active_choices = $scope.get_active_choices();
                    var active_choices_length = active_choices.length;
                    if (active_choices_length == 0) {
                        /* no choices are made, show the default title... */
                        return $sce.trustAsHtml($scope.title_placeholder);
                    }
                    else if (active_choices_length <= $scope.TITLE_LIMIT ) {
                        /* some choices are made, show them... */
                        var formatted_choices = $.map(active_choices, function(choice) {
                            return "\"" + choice.value + "\"";
                        })
                        return $sce.trustAsHtml(formatted_choices.join(", "));
                    }
                    else {
                        /* loads of choices are made, show some of them... */
                        var formatted_choices = $.map(active_choices.slice(0, $scope.TITLE_LIMIT), function(choice) {
                            return "\"" + choice.value + "\"";
                        })
                        return $sce.trustAsHtml(formatted_choices.join(", ") + "<em>...plus " + (active_choices_length - $scope.TITLE_LIMIT) + " more</em>");
                    }
                }
                $scope.get_active_choices = function() {
                    var active_choices = $.grep($scope.enumerationChoices, function(choice, index) {
                        return choice.is_active == true;
                    })
                    return active_choices;
                }
                $scope.select_choice = function(choice) {
                    var current_choices = $scope.current_model[$scope.enumerationName];
                    if ($scope.enumerationMultiple) {
                        var choice_index = current_choices.indexOf(choice.value);
                        if (choice.is_active && choice_index < 0) {
                            /* if the choice was selected and not in the corresponding JSON */
                            /* then add it to the JSON */
                            current_choices.push(choice.value)
                        }
                        else if (!choice.is_active && choice_index >= 0) {
                            /* if the choice was de-selected and previously in the correspnding JSON */
                            /* then remove it from the JSON */
                            current_choices.splice(choice_index, 1)
                        }
                    }
                    else {
                        if (choice.is_active) {
                            /* if the choice was selected... */
                            /* then inactivate every other choice, clear the corresponding JSON object and replace it w/ the choice's value */
                            $.each($scope.enumerationChoices, function (index, c) {
                                if (c != choice) {
                                    c.is_active = false;
                                }
                            });
                            current_choices.splice(0, current_choices.length);
                            current_choices.push(choice.value);
                        }
                        else {
                            /* if the choice was de-selected... */
                            /* then just clear the corresponding JSON object */
                            current_choices.splice(0, current_choices.length);
                        }
                    }
                    $scope.current_model[$scope.enumerationName] = current_choices;
                    $scope.enumerationFunction()();  /* call the fn associated w/ changing an enumeration */
                }
            }
        }
    }]);

    /******************/
    /* load-on-demand */
    /******************/

    app.directive("section", ['$http', '$compile', '$global_services', function($http, $compile, $global_services) {
        return {
            restrict: "EAC",
            replace: false,
            link: function(scope, element, attrs) {
                /* note that ng converts everything to camelCase */
                var model = attrs["modelToWatch"];
                var watched_name = model + ".display_detail";

                scope.$watch(watched_name, function(is_displayed) {

                   if (is_displayed && !$(element).hasClass("loaded")) {
                       var section_type = attrs["sectionType"];
                       var model_key = attrs["key"];
                       var model_index = attrs["index"];

//                       if (section_type.indexOf("subform") != -1) {
//                           /* unlike the regular sections, a 'subform' section moves the viewpane */
//                           /* to the top in preparation for displaying a modal dialog */
//                           $('html, body').animate({
//                               scrollTop: $(element).offset().top
//                           }, 2000);
//                       }

                       $global_services.setBlocking(true);
                       var url = "/services/load_section/" + section_type + "/";
                       var data = "session_key=" + session_key + "&key=" + model_key + "&index=" + model_index;
                       $http({
                            method: "POST",
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                            url: url,
                            data: data
                       })
                       .success(function(result) {
                            var content = $compile(result)(scope);
                            $(element).html(content);
                            init_widgets(selects, $(element).find(".select"));
                            init_widgets(helps, $(element).find(".help"));
                       })
                       .error(function(error) {
                            $(element).append("<p class='documentation'>error loading section</p>");
                            console.log(error);
                            console.log(error.data);
                       }).finally(function() {
                            $(element).addClass("loaded");
                            $global_services.setBlocking(false);
                       });
                   }
                });
            }
        }
    }]);


    app.directive('tree_bak', function() {
        /* this directive calls itself (in the template); supposedly, that's a really hard thing to do */
        /* but as of version 1.5 it seems to be built-in, (w/out having to recompile nested templates) */
        return {
            restrict: "EA",
            replace: false,
            scope: {
                nodes: '=',
                depth: '=?'
                /* TODO: 2 more scope variables bound to functions ('&') notation: for showing / hiding and enabling / disabling */
            },
            templateUrl: '/static/questionnaire/templates/q_ng_tree.html',
            link: function($scope, $element, $attrs) {
                $scope.expanded = true;
                $scope.depth = angular.isDefined($scope.depth) ? parseInt($scope.depth) : 0;
                $scope.has_subnodes = function(node) {
                    return node["nodes"].length > 0;
                }
                $scope.get_depth_as_array = function() {
                    /* in theory, I ought to be able to just write 'return new Array($scope.depth)' */
                    /* but that doesn't work consistently */
                    var depth_array = new Array();
                    for (var i=0; i<$scope.depth; i++) {
                        depth_array.push(1);
                    }
                    return depth_array;
                }
                $scope.select_node = function(node) {
                    node.is_selected = true;
                    /* show / hide stuff in the pane */
                    /* map the value to 'display_detail' of the correct bit in the parent model */
                }
                $scope.toggle_node_activation = function(node) {
                    /* enable / disable stuff in the pane */
                    /* map the value to 'is_active' of the correct bit in the parent model */
                    $.each(node["nodes"], function(i, n) {
                        n.is_active = node.is_active;
                        $scope.toggle_node_activation(n);
                    });
                }
            }
        };
    });

    var tree_node_template = '' +
        '<div class="list-group-item" ng-class="{\'selected\': node.is_selected, \'inactive\': !node.is_active}" ng-click="select_node(node)">' +
            '<span class="spacer" ng-repeat="i in get_depth_as_array() track by $index"/>' +
            '<span class="help" data-toggle="tooltip" title="{{node.documentation}}">{{node.name}}</span>' +
            '<input type="checkbox" class="pull-right" ng-model="node.is_active" ng-click="toggle_node_activation(node)">' +
        '</div>' +
        '<div ng-repeat="subnode in node.nodes">' +
            '<tree node="subnode" depth="depth + 1"/>' +
        '</div>';

    app.directive("tree2", ['$http', '$compile', function($http, $compile) {
        return {
            restrict: "EA", /* E: element, A: attribute, C: class */
            replace: false,
            scope: {
                foo: "=",
                node: "=",
                depth: '=?'
            },
//            templateUrl: '/static/questionnaire/templates/q_ng_tree.html',
            link: function(scope, element, attrs) {

                scope.$watch("foo", function(newVal, oldVal) {
                    if (newVal) {
                        scope.depth = angular.isDefined(scope.depth) ? parseInt(scope.depth) : 0;
                        scope.has_subnodes = function(node) {
                            return node["nodes"].length > 0;
                        }
                        scope.get_depth_as_array = function() {
                            /* in theory, I ought to be able to just write 'return new Array($scope.depth)' */
                            /* but that doesn't work consistently */
                            var depth_array = new Array();
                            for (var i=0; i<scope.depth; i++) {
                                depth_array.push(1);
                            }
                            return depth_array;
                        }
                        scope.select_node = function(node) {
                            node.is_selected = true;
                            /* show / hide stuff in the pane */
                            /* map the value to 'display_detail' of the correct bit in the parent model */
                        }
                        scope.toggle_node_activation = function(node) {
                            /* enable / disable stuff in the pane */
                            /* map the value to 'is_active' of the correct bit in the parent model */
                            $.each(node["nodes"], function(i, n) {
                                n.is_active = node.is_active;
                                scope.toggle_node_activation(n);
                            });
                        }
                        var compileFn = $compile(tree_node_template);
                        var content = compileFn(scope);
                        $(element).html(content);

                    }
                }, true);
            }
        }
    }]);

    app.directive('tree3', function() {
        /* this directive calls itself (in the template); supposedly, that's a really hard thing to do */
        /* but as of version 1.5 it seems to be built-in, (w/out having to recompile nested templates) */
        return {
            restrict: "EA",
            replace: false,
            scope: {
                nodes: '=',
                depth: '=?'
                /* TODO: 2 more scope variables bound to functions ('&') notation: for showing / hiding and enabling / disabling */
            },
            templateUrl: '/static/questionnaire/templates/q_ng_tree.html',
            link: function($scope, $element, $attrs) {
                $scope.expanded = true;
                $scope.depth = angular.isDefined($scope.depth) ? parseInt($scope.depth) : 0;
                $scope.has_subnodes = function(node) {
                    return node["nodes"].length > 0;
                }
                $scope.get_depth_as_array = function() {
                    /* in theory, I ought to be able to just write 'return new Array($scope.depth)' */
                    /* but that doesn't work consistently */
                    var depth_array = new Array();
                    for (var i=0; i<$scope.depth; i++) {
                        depth_array.push(1);
                    }
                    return depth_array;
                }
                $scope.select_node = function(node) {
                    node.is_selected = true;
                    /* show / hide stuff in the pane */
                    /* map the value to 'display_detail' of the correct bit in the parent model */
                }
                $scope.toggle_node_activation = function(node) {
                    /* enable / disable stuff in the pane */
                    /* map the value to 'is_active' of the correct bit in the parent model */
                    $.each(node["nodes"], function(i, n) {
                        n.is_active = node.is_active;
                        $scope.toggle_node_activation(n);
                    });
                }
            }
        };
    });

    /******************************/
    /* client-side error handling */
    /******************************/

    /* (these mostly just call the corresponding fns in "q_validators.js") */

    app.directive('validatenobadchars', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$validators.validatenobadchars = function(modelValue, viewValue) {
                    if (ctrl.$isEmpty(modelValue)) {
                        // consider empty models to be valid
                        return true;
                    }

                    return validate_no_bad_chars(viewValue);
                };
            }
        };
    });

    app.directive('validatenotblank', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$validators.validatenotblank = function(modelValue, viewValue) {
                    if (ctrl.$isEmpty(modelValue)) {
                        // consider empty models to be valid
                        return true;
                    }

                    return validate_not_blank(viewValue);
                };
            }
        };
    });

    app.directive('validatenospaces', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$validators.validatenospaces = function(modelValue, viewValue) {
                    if (ctrl.$isEmpty(modelValue)) {
                        // consider empty models to be valid
                        return true;
                    }

                    return validate_no_spaces(viewValue);
                };
            }
        };
    });

    app.directive('validatenoreservedwords', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$validators.validatenoreservedwords = function(modelValue, viewValue) {
                    if (ctrl.$isEmpty(modelValue)) {
                        // consider empty models to be valid
                        return true;
                    }

                    return validate_no_reserved_words(viewValue);
                };
            }
        };
    });

    app.directive('validatenoprofanities', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$validators.validatenoprofanities = function(modelValue, viewValue) {
                    if (ctrl.$isEmpty(modelValue)) {
                        // consider empty models to be valid
                        return true;
                    }

                    return validate_no_profanities(viewValue);
                };
            }
        };
    });

    /******************************/
    /* server-side error handling */
    /******************************/

    app.directive('servererror', function() {
        /* this is a bit confusing... */
        /* "QForm.add_server_errors_to_field" adds this directive to any field that can produce a server error */
        /* "QForm.add_custom_errors" adds placeholders to the djangular-generated error elements for fields */
        /* where there is a server error, the DRF API will return a JSON array of errors keyed by field_name */
        /* it is the responsibility of the submit fn to add those errors to the global $scope.server_errors array */
        /* (which is what the aforementioned placeholders point to); it is also its responsibility to change the validity of djangular fields */
        /* finally, this directive adds a watch on the field's underlying ng-model; the first time it changes after a server error, its validity is reset */
        return {
            restrict: "A",
            require: "ngModel",
            require: '^form',  /* this makes sure that "ctrl" below is an ng-form element */
            link: function(scope, element, attrs, ctrl) {
                var model = attrs["ngModel"];
                var field_name = attrs["name"];
                scope.$watch(model, function () {
                    if ($(element).hasClass("ng-invalid-server")) {
                        ctrl[field_name].$setValidity('server', true);
                        $(element).removeClass("ng-invalid-server");
                    }
                });
            }
        }
    });

    /***********/
    /* THE END */
    /***********/

})();