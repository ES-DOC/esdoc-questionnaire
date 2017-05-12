/* q_validators */

/* custom client-side validation fns */
/* used by Angular */
/* see "QForm.get_field_errors" and "QForm.add_custom_potential_errors_to_field" */

function validate_no_bad_chars(value) {
    var BAD_CHARS_REGEX = /[\\\/\*<>%#\{\}\[\]$|]/g;

    if (value.match(BAD_CHARS_REGEX)) {
        return false;
    }
    else {
        return true;
    }
}

function validate_not_blank(value) {
    /* note that completely empty inputs don't get passed onto ng-validation */
    /* I can get around this by adding "ng-trim: false" */
    /* see, for example, how "enumeration_other_value" is initialized in QPropertyRealizationForm */

    var SPACES_REGEX = /\s/g;

    var trimmed_value = value.replace(SPACES_REGEX, '');

    if (!trimmed_value.length) {
        return false;
    }
    else {
        return true;
    }
}

function validate_no_spaces(value) {
    var SPACES_REGEX = /\s/g;

    if (value.match(SPACES_REGEX)) {
        return false;
    }
    else {
        return true;
    }
}

/* assumes that RESERVED_WORDS has been defined in q_base.html */
/* using a custom tag that provides external content loaded by Django */

function validate_no_reserved_words(value) {
    if (RESERVED_WORDS.indexOf(value) != -1) {
        return false;
    }
    else {
        return true;
    }
}

/* assumes that PROFANITIES_LIST has been defined in q_base.html */
/* using a custom tag that provides external content loaded by Django */

function validate_no_profanities(value) {
    for (var i=0; i<PROFANITIES_LIST.length; i++) {
        profanity = PROFANITIES_LIST[i];
        /* this tries to avoid the "scunthorpe problem" by only checking for complete words */
        var PROFANITY_REGEX =  "\\b" + profanity + "\\b";
        if (value.match(PROFANITY_REGEX)) {
            return false;
        }
    }
    return true;
}
