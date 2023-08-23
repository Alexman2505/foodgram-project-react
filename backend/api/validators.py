import re

from django.core.exceptions import ValidationError


def validate_username(value):
    invalid_chars = re.sub(r'^[\w.@+-]+$', '', value)

    if value.lower() == 'me':
        raise ValidationError('Имя пользователя "me" недопустимо.')
    if invalid_chars:
        raise ValidationError(
            "Имя пользователя содержит недопустимые символы: "
            f"{', '.join(invalid_chars)}"
        )
    return value
