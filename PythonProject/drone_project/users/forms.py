from django import forms
from django.core.validators import RegexValidator
from .models import CustomUser


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField(
        validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式不正确')]
    )

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'username', 'password']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('手机号已被注册')
        return phone
