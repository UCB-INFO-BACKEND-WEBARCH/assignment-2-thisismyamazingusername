from marshmallow import Schema, ValidationError, fields, validate

from app.models import Category


HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"


class CategorySummarySchema(Schema):
    id = fields.Int(required=True)
    name = fields.Str(required=True)
    color = fields.Str(allow_none=True)


class TaskResponseSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    completed = fields.Bool(required=True)
    due_date = fields.DateTime(allow_none=True)
    category_id = fields.Int(allow_none=True)
    category = fields.Nested(CategorySummarySchema, allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)


class TaskCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False, allow_none=True, validate=validate.Length(max=500))
    due_date = fields.DateTime(required=False, allow_none=True)
    category_id = fields.Int(required=False, allow_none=True)

    def validate_category(self, category_id):
        if category_id is None:
            return

        category = Category.query.get(category_id)
        if category is None:
            raise ValidationError({"category_id": ["Category does not exist."]})

    @staticmethod
    def _is_empty_string(value):
        return isinstance(value, str) and value.strip() == ""

    def validate_title_not_blank(self, title):
        if self._is_empty_string(title):
            raise ValidationError({"title": ["Field may not be blank."]})

    def load(self, data, *args, **kwargs):
        loaded = super().load(data, *args, **kwargs)
        self.validate_title_not_blank(loaded["title"])
        self.validate_category(loaded.get("category_id"))
        return loaded


class TaskUpdateSchema(Schema):
    title = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False, allow_none=True, validate=validate.Length(max=500))
    due_date = fields.DateTime(required=False, allow_none=True)
    category_id = fields.Int(required=False, allow_none=True)
    completed = fields.Bool(required=False)

    def validate_category(self, category_id):
        if category_id is None:
            return

        category = Category.query.get(category_id)
        if category is None:
            raise ValidationError("Category does not exist.")

    @staticmethod
    def _is_empty_string(value):
        return isinstance(value, str) and value.strip() == ""

    def load(self, data, *args, **kwargs):
        loaded = super().load(data, *args, **kwargs)
        if "title" in loaded and self._is_empty_string(loaded["title"]):
            raise ValidationError({"title": ["Field may not be blank."]})

        if "category_id" in loaded:
            try:
                self.validate_category(loaded.get("category_id"))
            except ValidationError as error:
                raise ValidationError({"category_id": error.messages}) from error

        return loaded


class CategoryCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    color = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(HEX_COLOR_PATTERN, error="Not a valid hex color format."),
    )

    @staticmethod
    def _is_empty_string(value):
        return isinstance(value, str) and value.strip() == ""

    def load(self, data, *args, **kwargs):
        loaded = super().load(data, *args, **kwargs)
        if self._is_empty_string(loaded["name"]):
            raise ValidationError({"name": ["Field may not be blank."]})
        return loaded
