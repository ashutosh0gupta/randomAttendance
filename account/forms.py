from django import forms


class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=64,
    min_length=1,widget=forms.TextInput(
        attrs={
            'class':'form-control',
            'placeholder':'cse username',
        }
    ))

    password = forms.CharField(
        widget = forms.PasswordInput(
            attrs={
                'class':'form-control',
                'placeholder':'********',
            }
        )
    )