import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_username(value):
    """Кастомный валидатор для проверки допустимых символов в username."""
    pattern = r'^[\w.@+-]+\Z'
    if not re.fullmatch(pattern, value):
        invalid_chars = set(re.sub(pattern, '', value))
        raise ValidationError(
            _('Недопустимые символы в имени пользователя: %(chars)s'),
            code='invalid_username',
            params={'chars': ''.join(invalid_chars)}
        )
