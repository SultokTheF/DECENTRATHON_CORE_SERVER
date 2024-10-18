from celery import shared_task
from django.utils import timezone
from twilio.rest import Client
from user.models import CustomUser
from api.models import Schedule, Record
from datetime import timedelta, datetime


TWILIO_ACCOUNT_SID = 'AC8a0514493862a7c1b2357b4156b05ecb'
TWILIO_AUTH_TOKEN = '6d5022469449fdeeeca39f7adda3117e'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'

# Настройка клиента Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@shared_task
def notify_users_two_hours_before_lesson():
    """Уведомить пользователей, если их урок начнется через 2 часа."""
    now = timezone.now()
    two_hours_later = now + timedelta(hours=2)

    # Получить записи для занятий, которые начнутся в следующие 2 часа, и уведомление не было отправлено
    records = Record.objects.filter(
        is_canceled=False,
        notification_sent=False,
        schedule__status=True,
        schedule__date__gte=now.date(),
        schedule__date__lte=(now + timedelta(days=1)).date()
    )

    for record in records:
        schedule = record.schedule
        schedule_datetime = timezone.make_aware(datetime.combine(schedule.date, schedule.start_time))

        if now <= schedule_datetime <= two_hours_later:
            user = record.user
            if user.phone_number:
                try:
                    # Форматировать время начала урока как hh:mm
                    formatted_time = schedule.start_time.strftime('%H:%M')
                    message_body = f"Напоминание: Ваш урок '{schedule.section.name}' начнется через 2 часа в {formatted_time}. Будьте готовы!"
                    client.messages.create(
                        body=message_body,
                        from_=TWILIO_WHATSAPP_FROM,
                        to=f'whatsapp:{user.phone_number}'
                    )
                    # Отметить уведомление как отправленное
                    record.notification_sent = True
                    record.save(update_fields=['notification_sent'])
                except Exception as e:
                    print(f"Ошибка при отправке сообщения на {user.phone_number}: {str(e)}")
        else:
            continue


@shared_task
def send_welcome_message(user_id):
    """Отправить приветственное сообщение пользователю, который успешно зарегистрировался."""
    user = CustomUser.objects.get(id=user_id)
    if user.phone_number:
        client.messages.create(
            body=f"Добро пожаловать, {user.first_name}! Вы успешно зарегистрировались.",
            from_=TWILIO_WHATSAPP_FROM,
            to=f'whatsapp:{user.phone_number}'
        )
        print(f"Приветственное сообщение отправлено на {user.phone_number}")


@shared_task
def notify_user_after_recording(record_id):
    """Уведомить пользователя, когда он успешно записан на урок."""
    record = Record.objects.get(id=record_id)
    user = record.user
    schedule = record.schedule

    if user.phone_number:
        try:
            # Отправить сообщение WhatsApp о записи на занятие
            message_body = f"Вы успешно записаны на урок '{schedule.section.name}', который пройдет {schedule.date} в {schedule.start_time.strftime('%H:%M')}. Ждем вас!"
            client.messages.create(
                body=message_body,
                from_=TWILIO_WHATSAPP_FROM,
                to=f'whatsapp:{user.phone_number}'
            )
            print(f"Уведомление отправлено пользователю {user.phone_number} для записи на урок {schedule.section.name}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения на {user.phone_number}: {str(e)}")
