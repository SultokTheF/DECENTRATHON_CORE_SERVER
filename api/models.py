from django.db import models
from django.utils import timezone
from geopy.geocoders import GoogleV3
import qrcode
import io
from django.core.files.base import ContentFile
from user.models import CustomUser
from datetime import timedelta, datetime
import calendar
from .utils import parse_pdf, generate_test_from_syllabus


GOOGLE_API_KEY = 'AIzaSyBAVkETmTSFkRbC-Vix0DJ7HbjWYPQ8Xa8'

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf)
    image_stream = buf.getvalue()
    return ContentFile(image_stream)

class SectionCategory(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class Center(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to='center_images/', blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    users = models.ManyToManyField(CustomUser, related_name='editable_centers')

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            geolocator = GoogleV3(api_key=GOOGLE_API_KEY)
            location = geolocator.geocode(self.location)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
            else:
                raise ValueError(f"Unable to geocode location: {self.location}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

from datetime import timedelta, datetime
import calendar

class Section(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey('SectionCategory', related_name='sections', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='section_images/', blank=True, null=True)
    center = models.ForeignKey('Center', related_name='sections', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    # syllabus = models.ForeignKey('Syllabus', related_name='sections', on_delete=models.SET_NULL, null=True, blank=True)  # Ссылка на Syllabus
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    weekly_pattern = models.JSONField(default=list)

    def save(self, *args, **kwargs):
        # Генерация QR-кода
        super().save(*args, **kwargs)
        if not self.qr_code:
            qr_data = {'section_id': self.id}
            qr_code_file = generate_qr_code(qr_data)
            self.qr_code.save(f'{self.name}_qr.png', qr_code_file, save=False)
            super().save(update_fields=['qr_code'])

        # Генерация статичного расписания
        self.generate_static_schedule_for_next_month()

    def generate_static_schedule_for_next_month(self):
        today = timezone.now().date()
        first_day_of_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        last_day_of_next_month = first_day_of_next_month.replace(
            day=calendar.monthrange(first_day_of_next_month.year, first_day_of_next_month.month)[1])

        # Удаление предыдущего расписания для следующего месяца
        Schedule.objects.filter(section=self, date__gte=first_day_of_next_month,
                                date__lte=last_day_of_next_month).delete()

        # Генерация статичного расписания
        current_date = first_day_of_next_month
        while current_date <= last_day_of_next_month:
            day_name = current_date.strftime('%A')
            for pattern in self.weekly_pattern:
                if pattern['day'] == day_name:
                    start_time = datetime.strptime(pattern['start_time'], '%H:%M').time()
                    end_time = datetime.strptime(pattern['end_time'], '%H:%M').time()

                    Schedule.objects.create(
                        section=self,
                        date=current_date,
                        start_time=start_time,
                        end_time=end_time,
                        capacity=20,  
                    )
            current_date += timedelta(days=1)

    def __str__(self):
        return self.name

    
from django.db import models

class Syllabus(models.Model):
    title = models.CharField(max_length=255)
    section = models.ForeignKey('Section', related_name='syllabuses', on_delete=models.CASCADE)  # Уникальный related_name для обратного доступа
    content = models.TextField()  

    def __str__(self):
        return self.title

    def generate_and_save_tests(self):
        """
        Генерация вопросов по содержимому силлабуса.
        """
        from .utils import generate_test_from_syllabus
        test_content = generate_test_from_syllabus(self.content, 5)
        print(f"Generated Test Content: {test_content}")  
        self.save_generated_tests(test_content)

    def save_generated_tests(self, test_content):
        """
        Сохранение сгенерированных тестов.
        """
        test_entries = test_content.strip().split("\n\n")
        letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

        for entry in test_entries:
            try:
                if "Correct Answer:" in entry:
                    parts = entry.split("Correct Answer:")
                    question_and_choices = parts[0].strip()
                    correct_answer_letter = parts[1].strip()

                    question_lines = question_and_choices.split("\n")
                    question = question_lines[0].strip()  # Вопрос
                    options = [option.strip()[3:] for option in question_lines[1:5]]  # Варианты ответа

                    # Преобразуем правильный ответ из буквы в индекс
                    correct_answer_index = letter_to_index.get(correct_answer_letter, None)

                    if correct_answer_index is not None:
                        # Сохранение вопроса и правильного ответа
                        test_question = TestQuestion.objects.create(
                            syllabus=self,
                            question=question,
                            options=options,  # Варианты ответа
                            correct_answer=correct_answer_index  # Номер правильного ответа
                        )
                        print(f"Saved Test Question: {test_question.question}, Correct Answer Index: {correct_answer_index}")
                    else:
                        print(f"Correct answer letter not found: {correct_answer_letter}")
            except Exception as e:
                print(f"Error processing entry: {entry} - {str(e)}")


class TestQuestion(models.Model):
    syllabus = models.ForeignKey(Syllabus, related_name='test_questions', on_delete=models.CASCADE)
    question = models.TextField()
    options = models.JSONField()  # Список из 4 вариантов ответа
    correct_answer = models.IntegerField()  # Номер правильного ответа (0, 1, 2, 3)

    def __str__(self):
        return self.question

class UserResults(models.Model):
    test_question = models.ForeignKey(TestQuestion, related_name="user_results", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name='user_results', on_delete=models.CASCADE)
    chosen_answer = models.IntegerField()  # Индекс выбранного ответа (0, 1, 2, 3)
    is_correct = models.BooleanField()  # Логическое поле для хранения результата: правильный/неправильный ответ
    points = models.IntegerField(default=0)  # Количество очков за вопрос
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User: {self.user.email}, Question: {self.test_question.question}, Correct: {self.is_correct}, Points: {self.points}"


class Subscription(models.Model):
    TYPE_CHOICES = (
        ('MONTH', 'Month'),
        ('6_MONTHS', '6 Months'),
        ('YEAR', 'Year')
    )

    name = models.CharField(max_length=255, default='Subscription')
    type = models.CharField(max_length=255, choices=TYPE_CHOICES, default='6_MONTHS')
    user = models.ForeignKey(CustomUser, related_name='subscriptions', on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_purchased = models.BooleanField(default=False)
    is_activated_by_admin = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        duration_mapping = {
            'MONTH': 30,
            '6_MONTHS': 180,
            'YEAR': 365
        }

        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=duration_mapping[self.type])

        self.is_active = self.end_date > timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.user.email} - {self.type}"

import requests

class Schedule(models.Model):
    section = models.ForeignKey(Section, related_name='schedules', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField()
    reserved = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    meeting_link = models.URLField(blank=True, null=True)  # New field

    def save(self, *args, **kwargs):
        if self.reserved >= self.capacity:
            self.status = False
        else:
            self.status = True
        super().save(*args, **kwargs)

    def start(self):
        url = "http://0.0.0.0:8050/meet/start/"
        response = requests.post(url)
        if response.status_code == 200:
            data = response.json()
            if 'whereby_link' in data:
                self.meeting_link = data['whereby_link']
                self.save(update_fields=['meeting_link'])
            else:
                raise ValueError("No meeting link returned from API.")
        else:
            raise ValueError(f"Failed to start meeting: {response.text}")

    def __str__(self):
        return f"{self.section.name} on {self.date}"

class Record(models.Model):
    user = models.ForeignKey(CustomUser, related_name='records', on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, related_name='records', on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    subscription = models.ForeignKey(Subscription, related_name='records', on_delete=models.CASCADE)
    is_canceled = models.BooleanField(default=False)  
    notification_sent = models.BooleanField(default=False)  # New field

    def cancel_reservation(self):
        if not self.is_canceled:  
            if self.schedule.reserved > 0:
                self.schedule.reserved -= 1
                self.schedule.save()
            self.is_canceled = True  
            self.save()

    def __str__(self):
        return f"{self.user.email} - {self.schedule.section.name}"

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks')
    text = models.TextField()
    stars = models.IntegerField(choices=RATING_CHOICES)
    center = models.ForeignKey('Center', on_delete=models.CASCADE, related_name='feedbacks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.email} - {self.stars} Stars"