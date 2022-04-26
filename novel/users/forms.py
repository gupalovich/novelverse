from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import get_user_model, forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserAdminChangeForm(forms.UserChangeForm):
    class Meta(forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }


class UserChangeForm(forms.UserChangeForm):

    class Meta(forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(forms.UserCreationForm):

    error_message = forms.UserCreationForm.error_messages.update(
        {"duplicate_username": _("This username has already been taken.")}
    )

    class Meta(forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
