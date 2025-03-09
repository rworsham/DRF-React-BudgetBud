from rest_framework.renderers import JSONRenderer
from decimal import Decimal


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        def format_decimal(value):
            if isinstance(value, Decimal):
                return f"{value:.2f}"
            return value

        def recursive_format(data):
            if isinstance(data, dict):
                return {key: recursive_format(value) for key, value in data.items()}
            elif isinstance(data, list):
                return [recursive_format(item) for item in data]
            else:
                return format_decimal(data)

        data = recursive_format(data)
        return super().render(data, accepted_media_type, renderer_context)