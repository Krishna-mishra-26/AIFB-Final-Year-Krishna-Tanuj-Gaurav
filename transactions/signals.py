# transactions/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from .utils import check_budget_alert

@receiver(post_save, sender=Transaction)
def transaction_alert(sender, instance, created, **kwargs):
    if created and instance.category_type == 'expense':
        check_budget_alert(instance.user)
