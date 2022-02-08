# Generated by Django 4.0.2 on 2022-02-08 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simple_music_service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='song',
            name='artist',
        ),
        migrations.AddField(
            model_name='song',
            name='artist',
            field=models.ManyToManyField(to='simple_music_service.Artist'),
        ),
    ]
