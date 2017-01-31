from django.core.exceptions import ValidationError
from jsonschema.exceptions import ValidationError as JSONValidationError
from jsonschema import validate as json_validate
import json


def validate_file_extension(value, valid_extensions):
    """
    Validator function to use with fileFields.
    Ensures the file attempting to be uploaded matches a set of extensions.
    :param value: file being validated
    :param valid_extensions: list of valid extensions
    """
    if not value.name.split(".")[-1] in valid_extensions:
        raise ValidationError("Invalid File Extension.")


def validate_file_schema(value, schema_path):
    """
    validator function to use with fileFields;
    validates a file against a JSON Schema.
    """
    import ipdb; ipdb.set_trace()
    try:
        with open(schema_path, 'r') as file:
            schema = json.load(file)
        file.closed
    except IOError:
        msg = "Unable to read from {0}".format(schema_path)
        raise ValidationError(msg)
    except ValueError:
        msg = "Malformed JSON content in {0}".format(schema_path)
        raise ValidationError(msg)
    try:
        content = json.load(value)
        json_validate(content, schema)
    except JSONValidationError as e:
        raise ValidationError(e.message)
