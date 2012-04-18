/* custom js for the django_cim application */

function removeForm(data) {
  alert(data);
};

function toggleFields(fields) {
    var len=fields.length;
    for(var i=0; i<len; i++) {
        var fieldName = fields[i];
        // could either be field:
        // TODO

        // or fieldset:
        var fieldset_selector = "fieldset[name="+fieldName+"]";
        $(fieldset_selector).toggle();                
    }
};

function toggleForm(activeForm,allForms) {
    var len=allForms.length;
    for(var i=0; i<len; i++) {
        var formName = allForms[i];
        var fieldset_selector = "fieldset[name="+formName+"]";
        if (activeForm == formName) {
            $(fieldset_selector).show();
        }
        else {
            $(fieldset_selector).hide();
        }
    }
};