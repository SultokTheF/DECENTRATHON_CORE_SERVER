from django.db import models

class Context(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Russian'),
        ('kk', 'Kazakh'),
    ]

    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    context = models.TextField()

    def __str__(self):
        return f"{self.get_language_display()}: {self.context[:50]}..."