/* q_base.js */
/* angular app for Questionnaire */
/* all page-specific apps inherit from this */


(function() {
    var app = angular.module("q_base", ["q_base", "ui.bootstrap", "angular-loading-bar"]);

    /* note my use of angular-loading-bar above */
    /* this intercepts every $http call and displays a tiny loading bar */
    /* (I have overwritten the CSS to make it bigger: see "q_bootstrap.less") */

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

    /* TODO: I DON'T ACTUALLY NEED AN ACCORDION CONTROLLER, DO I? */
    /*
    app.controller("AccordionController", ["$scope", function($scope) {
        $scope.close_others = false;
        $scope.items = [];
    }]);
    */

    /* track validity of dynamically-created forms */
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

    /* load-on-demand stuff */
    app.directive('section', ['$http', '$compile', function($http, $compile) {
        return {
            restrict: "EAC", /* E: element, A: attribute, C: class */
            link: function (scope, element, attrs) {
                /* note that ng converts everything to camelCase */
                var model = attrs["modelToWatch"];
                var watched_name = model + ".display_detail";

                scope.$watch(watched_name, function (is_displayed) {
                    if (is_displayed && !$(element).hasClass("loaded")) {

                        var url = "/services/load_section/" + attrs["sectionType"] + "/";
                        /* TODO: SEE COMMENT BELOW */
                        /*var data = {'session_key': session_key};*/
                        var data = "session_key=" + session_key + "&key=" + attrs["key"] + "&index=" + attrs["index"];
                        $http({
                            method: "POST",
                            url: url,
                            /* TODO: I DON'T UNDERSTAND THIS */
                            /* TODO: I OUGHT TO BE ABLE TO JUST PASS STRAIGHTFORWARD JSON (ie: "{'key1':'val1','key2':'val2'}) */
                            /* headers: {'Content-Type': 'application/json'}, */
                            /* TODO: BUT FOR SOME REASON I HAVE TO PASS URL-ENCODED DATA (ie: "key1=val1&key2=val2") */
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                            data: data
                        }).then(
                            function(result) {
                                /* success */

                                /* this took absolute ages to figure out */
                                /* in order for ng stuff to be applied */
                                /* I have to explicitly compile the template */
                                /* (see http://odetocode.com/blogs/scott/archive/2014/05/07/using-compile-in-angular.aspx) */
                                var compileFn = $compile(result.data);
                                var content = compileFn(scope);
                                $(element).html(content);
                                init_widgets(helps, $(element).find(".help"));
                                init_widgets(selects, $(element).find(".select"));
                            },
                            function(error) {
                                /* error */

                                $(element).append("<p class='documentation'>error loading section</p>")
                                console.log(error);
                            }
                        ).finally(
                            function() {
                                $(element).addClass("loaded");
                            }
                        );

                    }
                });
            }
        }
    }]);

    /* TODO: THIS  FN SHOULD BE CONSOLIDATED W/ THE ABOVE FN */
    /* TODO: B/C IT'S REALLY SIMILAR */
    app.directive("subformSection", ['$http', '$compile', function($http, $compile) {
        return {
            restrict: "EAC", /* E: element, A: attribute, C: class */
            link: function(scope, element, attrs) {
                /* note that ng converts everything to camelCase */
                var model = attrs["modelToWatch"];
                var watched_name = model + ".display_detail";

                scope.$watch(watched_name, function(is_displayed) {

                   if (is_displayed && !$(element).hasClass("loaded")) {

                       /*
                       unlike the regular 'section' directive, this 'subform_section' directive
                       moves the viewpane to the top in preparation for displaying a modal dialog
                       */
                       $('html, body').animate({
                           scrollTop: $(element).offset().top
                       }, 2000);

                       var url = "/services/load_subform_section/" + attrs["sectionType"] + "/";
                       var data = "session_key=" + session_key + "&key=" + attrs["key"] + "&index=" + attrs["index"] + "&scope=" + attrs["scope"];
                       $http({
                           method: "POST",
                           url: url,
                           headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                           data: data
                       }).then(
                           function(result) {
                               console.log(data)
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
                               console.log(error);
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

    /* TODO: THIS  FN SHOULD BE CONSOLIDATED W/ THE ABOVE FNS */
    /* TODO: B/C IT'S REALLY SIMILAR */
    app.directive('subformPropertySection', ['$http', '$compile', function($http, $compile) {
        return {
            restrict: "EAC", /* E: element, A: attribute, C: class */
            link: function (scope, element, attrs) {
                /* note that ng converts everything to camelCase */
                var model = attrs["modelToWatch"];
                var watched_name = model + ".display_detail";

                scope.$watch(watched_name, function (is_displayed) {
                    if (is_displayed && !$(element).hasClass("loaded")) {

                        var url = "/services/load_subform_section/" + attrs["sectionType"] + "/";
                        var data = "session_key=" + session_key + "&scope=" + attrs["scope"] + "&index=" + attrs["index"] + "&key=" + attrs["key"];
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

                                $(element).append("<p class='documentation'>error loading section</p>")
                                console.log(error);
                            }
                        ).finally(
                            function() {
                                $(element).addClass("loaded")
                                $(element).trigger("loaded")
                            }
                        );

                    }

                });
            }
        }
    }]);

    /* server-side error handling */

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

    /* client-side error handling */
    /* these mostly just call the corresponding fns in "q_validators.js" */

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

    // TODO: USING NG INSTEAD OF JQUERY (see "q_base.js") FOR THIS FUNCTIONALITY MIGHT BE NICE
    //app.controller("MessagesController", [ "$http", function($http) {
    //
    //    var messages_controller = this;
    //
    //    messages_controller.messages = [];  // initial data
    //
    //    this.check_messages = function() {
    //        $http.get("/services/messages/")
    //            .success(function (data) {
    //                messages_controller.messages = data;
    //
    //                $.each(messages_controller.messages, function (i, message) {
    //                    var box = bootbox.alert(message.text);
    //                    box.find(".modal-content").addClass(message.status);
    //                })
    //            })
    //
    //            .error(function (data) {
    //                console.log(data);
    //            });
    //    };
    //
    //    messages_controller.check_messages();
    //
    //}]);

})();

