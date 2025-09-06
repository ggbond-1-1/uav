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


class PasswordResetForm(forms.Form):
    phone_number = forms.CharField(
        label='手机号',
        max_length=15,
        validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式不正确')],
        widget=forms.TextInput(attrs={'placeholder': '请输入注册时使用的手机号'})
    )
    new_password = forms.CharField(
        label='新密码',
        widget=forms.PasswordInput(attrs={'placeholder': '请输入新密码'})
    )
    confirm_password = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={'placeholder': '请再次输入新密码'})
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('该手机号未注册')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('两次输入的密码不一致')
        
        return cleaned_data
