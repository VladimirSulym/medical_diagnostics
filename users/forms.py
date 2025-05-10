from django import forms
from django.contrib.auth.forms import UserCreationForm

from users.models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("last_name", "first_name", "middle_name", "phone", "birth_date", "email", "password1", "password2")

    def save(self, commit=True):
        try:
            user = super().save(commit=False)
            user.email = self.cleaned_data["email"]
            if commit:
                user.save()
            return user
        except Exception as e:
            raise forms.ValidationError(f"Ошибка при сохранении пользователя: {str(e)}")
