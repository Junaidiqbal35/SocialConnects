from django import forms
from django.contrib.auth.models import User
from .models import Profile


class ProfileForm(forms.ModelForm):
    """Form for updating profile information"""

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'location', 'birth_date', 'website',
                  'facebook', 'twitter', 'instagram', 'linkedin', 'is_private']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind/Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            })

            # Custom styling for checkbox
            if field_name == 'is_private':
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
                })


class UserForm(forms.ModelForm):
    """Form for updating user information"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind/Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            })