from celery import shared_task
from django.core.mail import send_mail
from .models import Settlement

@shared_task
def send_payment_reminders():
    unsettled = Settlement.objects.filter(is_settled=False)
    for settlement in unsettled:
        send_mail(
            'Group Payment Reminder',
            f'Hello {settlement.payer.username}, please settle ₹{settlement.amount} to {settlement.payee.username}.',
            'no-reply@finance-tracker.com',
            [settlement.payer.email],
            fail_silently=False,
        )
