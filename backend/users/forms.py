from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext_lazy as _


class CustomPasswordChangeForm(PasswordChangeForm):
    current_password = forms.CharField(
        label=_("Current password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'current-password', 'class': 'form-control'}
        ),
    )
    new_password = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password', 'class': 'form-control'}
        ),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['old_password'] = self.fields.pop('current_password')
        self.fields['new_password1'] = self.fields.pop('new_password')
        del self.fields['new_password2']

    def clean_new_password2(self):
        return self.cleaned_data['new_password1']
