from django.db import models
from django.contrib.auth.models import User

class UserType(models.Model):
    USER_TYPE_CHOICES = [
        ('non_ad', 'Non-AD User'),
        ('ad', 'AD User'),
        ('both', 'Both AD and Non-AD User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(
        max_length=23,
        choices=USER_TYPE_CHOICES,
        default='non_ad'
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
