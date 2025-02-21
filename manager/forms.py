from django import forms
from django.contrib.auth.models import User, Group
from .models import TicketAssignment

class EngineerModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.username

class TicketAssignmentForm(forms.ModelForm):
    assignee = EngineerModelChoiceField(
        queryset=User.objects.filter(groups__name='Engineer'),
        label='Assignee',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = TicketAssignment
        fields = '__all__'
