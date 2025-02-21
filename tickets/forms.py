from django import forms
from .models import Item, no_special_characters_validator
from django.contrib.auth.models import User, Group

class TicketCreationForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['category', 'subcategory', 'short_description','detailed_description']
    detashort_descriptioniled_description = forms.CharField(
        widget=forms.Textarea,
        validators=[no_special_characters_validator],
        help_text="A short description of the item."
    )
    detailed_description = forms.CharField(
        widget=forms.Textarea,
        validators=[no_special_characters_validator],
        help_text="A detailed description of the item."
    )

class AddStoreCodeForm(forms.Form):
    username = forms.ChoiceField(choices=[], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    store_code = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].choices = [(user.username, user.username) for user in User.objects.filter(groups__name='CFAPerson')]

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        store_code = cleaned_data.get('store_code')