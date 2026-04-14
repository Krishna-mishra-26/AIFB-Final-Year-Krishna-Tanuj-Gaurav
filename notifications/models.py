from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now

User = get_user_model()

class Notification(models.Model):
    RECIPIENT_CHOICES = [
        ('all', 'All Users'),
        ('premium', 'Premium Users'),
        ('free', 'Free Users'),
    ]

    recipients = models.CharField(max_length=10, choices=RECIPIENT_CHOICES,default="")
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=10, default='sent')
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return self.title

