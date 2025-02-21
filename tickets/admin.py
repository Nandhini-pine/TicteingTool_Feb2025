from django.contrib import admin
from . models import *

# Register your models here.

admin.site.register(Item)
admin.site.register(FileUpload)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(ApprovalMatrix)
admin.site.register(TicketFileTotalSize)
admin.site.register(StatusHistory)
admin.site.register(SeekAttachment)
admin.site.register(SeekClarificationHistory)

from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Store

class StoreAdminForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = '__all__'  # Include all fields from the Store model

    def clean_user(self):
        user = self.cleaned_data['user']
        store_person_group = Group.objects.get(name='CFAPerson')
        
        if user.groups.filter(pk=store_person_group.pk).exists():
            # Check if the user already has a store
            existing_store = Store.objects.filter(user=user).exclude(pk=self.instance.pk).first()
            if existing_store:
                raise forms.ValidationError("CFAPersons can have only one store.")
        return user

class StoreAdmin(admin.ModelAdmin):
    form = StoreAdminForm

admin.site.register(Store, StoreAdmin)

