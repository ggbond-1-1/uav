from django import forms
from django.core.validators import RegexValidator
from .models import CustomUser

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField(
        validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式不正确')]
    )
    id_number = forms.CharField(
        validators=[RegexValidator(r'^\d{17}[\dXx]$', '身份证号格式不正确')]
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'id_number', 'username', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('邮箱已被注册')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('手机号已被注册')
        return phone