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