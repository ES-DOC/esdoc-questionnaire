from django.db import models
import json
import re
from django.core.exceptions import ValidationError
from jsonschema.exceptions import ValidationError as JSONValidationError
from jsonschema.validators import validate as json_validate


class ThingJSONField(models.TextField):
    """
    encodes JSON in a text field
    optionally validates against a JSON Schema
    """

    def __init__(self, *args, **kwargs):
        self.json_schema = kwargs.pop("schema", None)
        super(ThingJSONField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """
        db to code; text to JSON object
        """
        if not value:
            return None
        try:
            # sometimes it's not _clean_ JSON
            # (for example, fixtures pollute these strings w/ unicode garbage)
            # so clean it up here...
            clean_value = re.sub(r"(u')(.*?)(')", r'"\2"', value)
            json_content = json.loads(clean_value)
            if self.json_schema:
                json_validate(json_content, self.json_schema)
            return json_content
        except ValueError:
            msg = "Malformed content used in {0}: '{1}'.".format(
                self.__class__.__name__,
                clean_value
            )
            raise ValidationError(msg)
        except JSONValidationError as e:
            msg = "Content used in {0} does not conform to schema: {1}".format(
                self.__class__.__name__,
                e.message
            )
            raise ValidationError(msg)

    def get_prep_value(self, value):
        """
        code to db; JSON to text
        """
        import ipdb; ipdb.set_trace()
        if not value:
            return None
        try:
            if self.json_schema:
                json_validate(value, self.json_schema)
            return json.dumps(value)
        except ValueError:
            msg = "Malformed content used in {0}: '{1}'.".format(
                self.__class__.__name__,
                value
            )
            raise ValidationError(msg)
        except JSONValidationError as e:
            msg = "Content used in {0} does not conform to schema: {1}".format(
                self.__class__.__name__,
                e.message
            )
            raise ValidationError(msg)

    def from_db_value(self, value, expression, connection, context):
        """
        does the same thing as "to_python",
        it's just called in different situations b/c of a quirk w/ Django 1.8
        (see https://docs.djangoproject.com/en/1.8/howto/custom-model-fields/)
        """
        return self.to_python(value)
