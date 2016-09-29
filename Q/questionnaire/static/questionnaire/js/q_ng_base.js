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

    app.controller("TabController", function() {
        /* simple little controller for dealing w/ tabs */
        this.tab = 1;
        this.selectTab = function(tab_id) {
            this.tab = tab_id;
        };
        this.isSelected = function(tab_id) {
            return this.tab === tab_id;
        };
    });

    app.controller("FieldsetController", function() {
        /* simple little controller for collapsible fieldsets */
        var fieldset_controller = this;
        fieldset_controller.is_collpased = false;
    });

    /*
    app.controller("AccordionController", ["$scope", function($scope) {
        // TODO: I DON'T ACTUALLY NEED AN ACCORDION CONTROLLER, DO I?
        $scope.close_others = false;
        $scope.items = [];
    }]);
    */

    /*
    // TODO: USING NG INSTEAD OF JQUERY (see "q_base.js") FOR THIS FUNCTIONALITY MIGHT BE NICE
    app.controller("MessagesController", [ "$http", function($http) {

        var messages_controller = this;
        messages_controller.messages = [];  // initial data

        this.check_messages = function() {
            $http.get("/services/messages/")
                .success(function (data) {
                    messages_controller.messages = data;
                    $.each(messages_controller.messages, function (i, message) {
                        var box = bootbox.alert(message.text);
                        box.find(".modal-content").addClass(message.status);
                    })
                })
                .error(function (data) {
                    console.log(data);
                });
        };

        messages_controller.check_messages();

    }]);
    */

    /*************/
    /* FACTORIES */
    /*************/

    /**************************************************************************/
    /* load initial model data & get submodels to map to (nested) controllers */
    /**************************************************************************/

    app.factory('$global_services', ['$http', function($http) {

        /*****************************/
        /* global app-wide variables */
        /*****************************/

        var _blocking = false;

        var _is_loaded = false;

	    var _DATA =  {};  /* (top-level controller resets this via AJAX) */

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
            stop: function(e, ui) {
                /* I AM NO LONGER DOING THIS... */
                /* THIS ASSUMES THAT THE ORDER OF ELEMENTS IN THE NG ARRAY ACTUALLY CHANGES */
                /* BUT I PREVENT THAT IN "update" BELOW */
                //var sorted_properties = ui.item.sortable.sourceModel;
                //$.each(sorted_properties, function(i, property) {
                //    property.order = i+1;
                //});
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

        /* TODO: THERE IS STILL AN ERROR IN THIS FN SOMEPLACE ?!? */
        /* TODO: THAT'S OKAY, THOUGH, I NEVER NEED TO CALL IT - RIGHT? */
        /* TODO: AND (EVEN IF IT WORKS), IT IS EXTREMELY INNEFFICIENT - RIGHT? */
        function get_path_from_model(target_model, current_obj, current_path) {
            /* given a model (part of _DATA), return a JSON "path" to that model */
            if (typeof current_obj == "undefined" || current_obj === null) {
    	        /* default value */
                current_obj = _DATA;
            }
            if (typeof current_path === "undefined" || current_path === null) {
    	        /* default value */
                current_path = "_DATA";
            }

            for (var key in current_obj) {
                var value = current_obj[key];
                if (value != null) {  /* some serialized values might be un-set; just ignore them */
                    var value_type = value.constructor;

                    /* value can either be an Array */
                    if (value_type === Array) {
                        if (value === target_model) {
                            return current_path + "." + key;
                        }
                        for (var i = 0; i < value.length; i++) {
                            if (value[i] === target_model) {
                                return current_path + "." + key + "[" + i + "]";
                            }
                            var result = get_path_from_model(target_model, value, current_path + "." + key + "[" + i + "]");
                            if (result) {
                                return result;
                            }
                        }
                    }

                    /* or value can be an Object itself */
                    else if (value_type === Object) {
                        if (value === target_model) {
                            return current_path + "." + key;
                        }
                        var result = get_path_from_model(target_model, value, current_path);
                        if (result) {
                            return result;
                        }
                    }

                    /* or value can something atomic */
                    else {
                        if (value === target_model) {
                            return current_path + "." + key;
                        }
                    }
                }
            }
            return false;
        };

        function get_model_from_path(path) {
            /* given a JSON path return model (part of _DATA) */

            path = path.split('.');
            var current_obj = _DATA;
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
            getPathFromModel: get_path_from_model,
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

    /***************************************************/
    /* track the validity of dynamically-created forms */
    /***************************************************/

    app.directive('watchFormValidity', function() {
        return {
            restrict: "A", /* E: element, A: attribute, C: class */
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

    /******************/
    /* LOAD-ON-DEMAND */
    /******************/

    app.directive("section", ['$http', '$compile', function($http, $compile) {
        return {
            restrict: "EAC", /* E: element, A: attribute, C: class */
            link: function(scope, element, attrs) {
                /* note that ng converts everything to camelCase */
                var model = attrs["modelToWatch"];
                var watched_name = model + ".display_detail";

                scope.$watch(watched_name, function(is_displayed) {

                   if (is_displayed && !$(element).hasClass("loaded")) {

                       var section_type = attrs["sectionType"];
                       var model_key = attrs["key"];
                       var model_index = attrs["index"];

                       if (section_type.indexOf("subform") != -1) {
                           /* unlike the regular sections, a 'subform' section moves the viewpane */
                           /* to the top in preparation for displaying a modal dialog */
                           $('html, body').animate({
                               scrollTop: $(element).offset().top
                           }, 2000);
                       }

                       var url = "/services/load_section/" + section_type + "/";
                       var data = "session_key=" + session_key + "&key=" + model_key + "&index=" + model_index;
                       $http({
                           method: "POST",
                           url: url,
                           headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                           data: data
                       }).then(
                           function(result) {
                               /* success */
                               var compileFn = $compile(result.data);
                               var content = compileFn(scope);
                               $(element).html(content);
                               init_widgets(helps, $(element).find(".help"));
                               init_widgets(selects, $(element).find(".select"));
                           },
                           function(error) {
                               /* error */
                               $(element).append("<p class='documentation'>error loading section</p>");
                               console.log(error.data);
                           }
                       ).finally(
                           function() {
                               $(element).addClass("loaded");
                           }
                       )
                   }
                });
            }
        }
    }]);


    /**********************/
    /* enumeration fields */
    /**********************/

    app.directive('enumeration', ['$filter', '$sce', function($filter, $sce) {
        return {
            restrict: "EA", /* E: element, A: attribute, C: class */
            scope: {
                enumerationName: '=',
                enumerationRequired: '=',
                enumerationChoices: '=',
                enumerationMultiple: '=?',
                enumerationFunction: '&'
            },
            template: function (element, attrs) {
                var template = '' +
                    '<div class="enumeration">' +
                    '   <button class="btn btn-primary" type="button" ng-click="open = !open">' +
                    '       <span ng-show="open" class="glyphicon glyphicon-triangle-bottom"></span>' +
                    '       <span ng-hide="open" class="glyphicon glyphicon-triangle-right"></span>' +
                    /* ng-bind-html automagically includes HTML in strings */
                    /* (see my use of "$sce.trustedHtml" below) */
                    '       &nbsp;<span ng-bind-html="getEnumerationLabel()"></span>' +
                    '   </button>' +
                    '   <ul class="list-group" ng-show="open">' +
                    '       <li class="list-group-item" ng-repeat="choice in enumerationChoices" ng-class="{\'selected\': choice.active}">' +
                    '           <label ng-class="{\'disabled\': current_model.is_nil}">' +
                    '               <input type="checkbox" ng-model="choice.active" ng-disabled="current_model.is_nil" ng-click="selectChoice(choice)"/>&nbsp;' +
                    '               {{ choice.name }}' +
                    '               <span ng-show="choice.documentation" class="help glyphicon glyphicon-info-sign pull-right" data-container="body" data-toggle="popover" data-placement="right" data-content="{{ choice.documentation }}"/>' +
                    '           </label>' +
                    '       </li>' +
                    '   </ul>' +
                    '</div> <!-- /.enumeration -->';
                element.html(template);
            },
            link: function ($scope, $element, $attrs) {

                /* set default values */
                $scope.enumeration_limit = 2;
                $scope.open = false;
                $scope.is_multiple = angular.isDefined($scope.enumerationMultiple) ? $scope.enumerationMultiple : false;
                if ($scope.is_multiple) {
                    $scope.enumeration_placeholder = $sce.trustAsHtml("<span class='placeholder'>Please select option(s)</span>");
                }
                else {
                    $scope.enumeration_placeholder = $sce.trustAsHtml("<span class='placeholder'>Please select an option</span>");
                }
                /* b/c the Q is so asynchronous, I need to wait to set "current_model" until the parent controller has loaded */
                $scope.loaded_enumeration = false;
                $scope.$watch(function () {
                        return $scope.$parent.isLoaded();
                    },
                    function(is_loaded) {
                        if (is_loaded && !$scope.loaded_enumeration) {

                            $scope.current_model = $scope.$parent.current_model;

                            /* now set the initial values */
                            var initial_choices = $scope.current_model[$scope.enumerationName]
                            if (initial_choices.constructor != Array) {
                                initial_choices = initial_choices.split('|');
                            };
                            $.each($scope.enumerationChoices, function(i, enumeration_choice) {
                                if (initial_choices.indexOf(enumeration_choice.value) != -1) {
                                    enumeration_choice.active = true;
                                }
                            });

                            /* also, initialize any custom widgets in the template _after_ content is loaded */
                            init_widgets(helps, $element.find(".help"));
                            $scope.loaded_enumeration = true;
                        }
                    }
                );

                $scope.getEnumerationLabel = function () {
                    var active_choices = $scope.getActiveChoices();
                    var active_choices_length = active_choices.length;
                    if (active_choices_length == 0) {
                        return $scope.enumeration_placeholder;
                    }
                    else if (active_choices_length <= $scope.enumeration_limit ){
                        var choices = $.map(active_choices, function(choice) {
                            return "\"" + choice.name + "\"";
                        });
                        return $sce.trustAsHtml(choices.join(", "));
                    }
                    else {
                        var choices = $.map(active_choices.slice(0,$scope.enumeration_limit), function(choice) {
                            return "\"" + choice.name + "\"";
                        });
                        return $sce.trustAsHtml(choices.join(", ") + " <em>...plus " + (active_choices_length - $scope.enumeration_limit) + " more</em>");
                    }
                };

                $scope.getActiveChoices = function() {
                    var active_choices = $.grep($scope.enumerationChoices, function(choice, index) {
                        return choice.active == true;
                    });
                    return active_choices
                };

                $scope.selectChoice = function(choice) {

                    var current_choices = $scope.current_model[$scope.enumerationName];
                    if (current_choices.constructor != Array) {
                        current_choices = current_choices.split('|');
                    };
                    if ($scope.is_multiple) {
                        var index = current_choices.indexOf(choice.value);
                        if (choice.active && index == -1) {
                            /* if the choice is selected and not in the model */
                            /* add it to the model */
                            current_choices.push(choice.value);
                        }
                        else if (!choice.active && index > -1) {
                            /* if the choice is de-selected and in the model */
                            /* remove it from the model */
                            current_choices.splice(index, 1)
                        }
                    }
                    else {
                        if (choice.active) {
                            /* if the choice is selected */
                            /* deselect other choices and set it to the model */
                            $.each($scope.enumerationChoices, function (index, c) {
                                if (c != choice) {
                                    c.active = false;
                                }
                            });
                            current_choices.splice(0, current_choices.length);
                            current_choices.push(choice.value);
                        }
                        else {
                            /* if the choice is de-selected */
                            /* clear the model */
                            current_choices.splice(0, current_choices.length);
                        }
                    }
                    $scope.current_model[$scope.enumerationName] = current_choices;
                    // if this enumeration is required, then trigger the change event
                    if ($scope.enumerationRequired) {
                        $scope.enumerationFunction()();
                    }

                };
            }
        }
    }]);

    /******************************/
    /* server-side error handling */
    /******************************/

    app.directive('servererror', function() {
        /* makes sure that if a "server" error has been detected, */
        /* modifying the offending field immediately reinstates its validity */
        return {
            require: 'ngModel',
            restrict: 'A',
            link: function(scope, elm, attrs, ctrl) {
                /* not all of these events are supported by all browsers */
                /* but between them, they do a pretty good job */
                /* (the "change" event on its own was only firing when focus was lost) */
                $(elm).on("change keyup paste input", function() {
                    scope.$apply(function() {
                        ctrl.$setValidity('server', true)
                    });
                });
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

    app.directive('validatenobadsuggestionchars', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$validators.validatenobadsuggestionchars = function(modelValue, viewValue) {
                    if (ctrl.$isEmpty(modelValue)) {
                        // consider empty models to be valid
                        return true;
                    }

                    return validate_no_bad_suggestion_chars(viewValue);
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

    /***********/
    /* THE END */
    /***********/

})();