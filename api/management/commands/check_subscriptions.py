# your_app/management/commands/check_subscriptions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import Subscription, Enrollment

class Command(BaseCommand):
    help = 'Checks and deactivates expired subscriptions'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_by_date = Subscription.objects.filter(expiration_date__lt=now, is_active=True)
        for subscription in expired_by_date:
            subscription.is_active = False
            subscription.save()
            self.stdout.write(self.style.SUCCESS(f'Deactivated subscription {subscription.id} due to expiration date'))

        all_subscriptions = Subscription.objects.filter(is_active=True)
        for subscription in all_subscriptions:
            lesson_limit = int(subscription.type.split()[0])  # extract the number of lessons from the type
            attended_lessons = Enrollment.objects.filter(subscription=subscription, confirmed=True).count()
            if attended_lessons >= lesson_limit:
                subscription.is_active = False
                subscription.save()
                self.stdout.write(self.style.SUCCESS(f'Deactivated subscription {subscription.id} due to lesson limit'))
