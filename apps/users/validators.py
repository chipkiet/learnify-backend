import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class LetterAndNumberValidator:
    """
    Validate whether the password contains at least one letter and one number.
    """
    def validate(self, password, user=None):
        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError(
                _("Mật khẩu phải chứa ít nhất 1 chữ cái."),
                code='password_no_letter',
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Mật khẩu phải chứa ít nhất 1 chữ số."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _("Mật khẩu phải chứa ít nhất 1 chữ cái và 1 chữ số.")
