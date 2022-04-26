# Generated by Django 3.2.13 on 2022-04-26 08:21

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(default='', max_length=255, verbose_name='Title')),
                ('title_sm', models.CharField(blank=True, default='', max_length=50, verbose_name='Title short')),
                ('slug', models.SlugField(default='', max_length=255, unique=True)),
                ('author', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=112), blank=True, default=list, size=None)),
                ('allow_comments', models.BooleanField(default=True, verbose_name='allow comments')),
                ('country', models.CharField(blank=True, choices=[('china', 'China'), ('korea', 'Korea'), ('japan', 'Japan'), ('original', 'Original')], default='china', max_length=55)),
                ('similar', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, default=list, size=None)),
                ('description', models.TextField(blank=True, default='', verbose_name='Description')),
                ('volumes', django.contrib.postgres.fields.ArrayField(base_field=models.SmallIntegerField(default=1), blank=True, default=list, size=None)),
                ('chapters_count', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Chapters')),
                ('chapters_release', models.SmallIntegerField(blank=True, default=0, null=True, verbose_name='Chapters update')),
                ('poster', models.ImageField(blank=True, default='posters/default.jpg', null=True, upload_to='posters/', verbose_name='Poster')),
                ('votes', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Votes')),
                ('ranking', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Ranking')),
                ('rating', models.FloatField(blank=True, default=0.0, verbose_name='Rating')),
                ('recommended', models.BooleanField(blank=True, default=False)),
                ('visit', models.CharField(blank=True, choices=[('webnovel', 'Webnovel'), ('boxnovel', 'Boxnovel'), ('wuxiaworld', 'Wuxia World'), ('gravitytails', 'Gravity Tails'), ('flyinglines', 'Flying Lines'), ('lnmtl', 'LNMTL'), ('other', 'Other')], default='webnovel', max_length=55)),
                ('visit_id', models.CharField(blank=True, default='', max_length=255, verbose_name='Visit id')),
                ('visited', models.BooleanField(blank=True, default=False)),
                ('revisit', models.CharField(blank=True, choices=[('webnovel', 'Webnovel'), ('boxnovel', 'Boxnovel'), ('wuxiaworld', 'Wuxia World'), ('gravitytails', 'Gravity Tails'), ('flyinglines', 'Flying Lines'), ('lnmtl', 'LNMTL'), ('other', 'Other')], default='webnovel', max_length=55)),
                ('revisit_id', models.CharField(blank=True, default='', max_length=255, verbose_name='Revisit id')),
                ('revisited', models.BooleanField(blank=True, default=False)),
                ('status', models.IntegerField(choices=[(0, 'draft'), (1, 'published')], db_index=True, default=0)),
                ('status_release', models.IntegerField(choices=[(0, 'ongoing'), (1, 'onhold'), (2, 'abandoned'), (3, 'completed')], default=0)),
                ('published_at', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status', when={'published'})),
            ],
            options={
                'verbose_name': 'Book',
                'verbose_name_plural': 'Books',
            },
        ),
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
        migrations.CreateModel(
            name='BookGenre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(default='', max_length=112, verbose_name='Genre')),
                ('slug', models.SlugField(max_length=112, unique=True)),
            ],
            options={
                'verbose_name': 'Book Genre',
                'verbose_name_plural': 'Book Genres',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BookTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(default='', max_length=112, verbose_name='Tag')),
                ('slug', models.SlugField(max_length=112, unique=True)),
            ],
            options={
                'verbose_name': 'Book Tag',
                'verbose_name_plural': 'Book Tags',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BookChapter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('allow_comments', models.BooleanField(default=True, verbose_name='allow comments')),
                ('c_id', models.IntegerField(blank=True, default=0, null=True, verbose_name='Chapter ID')),
                ('title', models.CharField(default='', max_length=255, verbose_name='Title')),
                ('slug', models.SlugField(default='', max_length=255, unique=True)),
                ('text', models.TextField(default='')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookchapters', related_query_name='bookchapter', to='books.book')),
            ],
            options={
                'verbose_name': 'Book Chapter',
                'verbose_name_plural': 'Book Chapters',
            },
        ),
        migrations.AddField(
            model_name='book',
            name='bookgenre',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='books', related_query_name='book', to='books.bookgenre'),
        ),
        migrations.AddField(
            model_name='book',
            name='booktag',
            field=models.ManyToManyField(blank=True, related_name='books', to='books.BookTag'),
        ),
    ]
