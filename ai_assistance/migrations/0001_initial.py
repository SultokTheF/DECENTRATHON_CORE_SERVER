# Generated by Django 5.0.5 on 2024-10-18 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Context',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('ru', 'Russian'), ('kk', 'Kazakh')], max_length=2)),
                ('context', models.TextField()),
            ],
        ),
    ]