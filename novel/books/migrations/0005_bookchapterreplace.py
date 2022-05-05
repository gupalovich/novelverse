# Generated by Django 3.2.13 on 2022-05-03 10:06

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0004_book_view_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookChapterReplace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('replace', models.CharField(default='', max_length=355, verbose_name='Replace')),
                ('replace_to', models.CharField(blank=True, default='', max_length=355, verbose_name='Replace to')),
            ],
            options={
                'verbose_name': 'Book Chapter Replace',
                'verbose_name_plural': 'Book Chapter Replaces',
            },
        ),
    ]