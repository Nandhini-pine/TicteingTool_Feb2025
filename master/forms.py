# forms.py
from django import forms
from tickets.models import *
from django.contrib.auth.models import User, Group
import re
from django.forms import EmailField, ModelMultipleChoiceField, CharField, ValidationError
from django.forms.widgets import EmailInput, SelectMultiple
from django.forms import PasswordInput
from django.core.exceptions import ValidationError
from .models import *
from django.forms import ModelForm

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ['category', 'name', 'functionality', 'technically']



class EditSubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ['category', 'name', 'functionality', 'technically']
    
    # Custom validation for the 'category' and 'name' combination
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        name = cleaned_data.get('name')
        
        # Ensure no duplicate category and subcategory combination
        if Subcategory.objects.filter(category=category, name=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This combination of Category and Subcategory already exists.")
        return cleaned_data

class ApprovalMatrixForm(forms.ModelForm):
    class Meta:
        model = ApprovalMatrix
        fields = ['functionally', 'technically', 'approval']

    def clean(self):
        cleaned_data = super().clean()
        functionally = cleaned_data.get('functionally')
        technically = cleaned_data.get('technically')

        if ApprovalMatrix.objects.filter(functionally=functionally, technically=technically).exists():
            raise forms.ValidationError('The combination of functionality, technicality, and approval already exists.')

        return cleaned_data

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User, Group
from django.core.validators import EmailValidator

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email'] 

    email = forms.EmailField(validators=[EmailValidator()], 
                             widget=forms.EmailInput(attrs={'class': 'form-control'})) 
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Select Group",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_groups'}) 
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")

        # Ensure the username contains only alphabetic characters
        if not re.match("^[a-zA-Z]+$", username):
            raise forms.ValidationError("Username should only contain alphabetic characters (no numbers or special characters).")
        
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists. Please choose a different one.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email=email).exists(): 
            raise forms.ValidationError("Email address already exists.") 
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].empty_label = "Select an option"

    def save(self, commit=True):
        user = super().save(commit=False) 
        if commit:
            user.save()  # Save the user instance first to get the 'id'
        if self.cleaned_data.get('groups'):
            user.groups.set([self.cleaned_data.get('groups')]) 
        user_type_instance, created = UserType.objects.get_or_create(user=user)
        user_type_instance.user_type = 'non_ad'
        user_type_instance.save()

        return user
    
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'groups']  # Include groups field

    email = forms.EmailField(validators=[EmailValidator()], 
                             widget=forms.EmailInput(attrs={'class': 'form-control'})) 
    groups = forms.ModelMultipleChoiceField(  # Use ModelMultipleChoiceField for multiple group selection
        queryset=Group.objects.all(),
        label="Select Group",
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'id': 'id_groups'}) 
    )
    password1 = CharField(label="New Password (optional)", required=False, widget=PasswordInput(attrs={'class': 'form-control'}))
    password2 = CharField(label="Confirm New Password (optional)", required=False, widget=PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].empty_label = "Select an option"

        if self.instance:
            self.fields['email'].initial = self.instance.email 
            self.fields['groups'].initial = self.instance.groups.all()  # Get all groups for the user

    def clean_username(self):
        username = self.cleaned_data.get("username")

        # Ensure the username contains only alphabetic characters
        if not re.match("^[a-zA-Z]+$", username):
            raise forms.ValidationError("Username should only contain alphabetic characters (no numbers or special characters).")

        # Check if the username is unique only if it has been changed
        if username != self.instance.username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists. Please choose a different one.")
        return username
    def clean_email(self):
        email = self.cleaned_data.get("email")

        # Check if the email is unique if it has been changed
        if email != self.instance.email and User.objects.filter(email=email).exists(): 
            raise forms.ValidationError("Email address already exists.") 
        return email 
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password1 != password2:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get("password1")

        if password1:
            user.set_password(password1) 
        if commit:
            user.save()
        return user

class AdUserCreationForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'groups'] 

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists(): 
            raise ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(id=self.instance.id).exists(): 
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False) 
        if commit:
            user.save()  # Save the user before creating UserType
        user.groups.set(self.cleaned_data.get('groups')) 

        user_type_instance, created = UserType.objects.get_or_create(user=user)
        user_type_instance.user_type = 'ad'
        user_type_instance.save()
        return user