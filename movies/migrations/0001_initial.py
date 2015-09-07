# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='GeocodingCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('data', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('location', models.CharField(unique=True, max_length=200)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=200)),
                ('year', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='MovieActor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='MovieLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fun_facts', models.TextField(null=True)),
                ('location', models.ForeignKey(to='movies.Location')),
                ('movie', models.ForeignKey(to='movies.Movie')),
            ],
        ),
        migrations.CreateModel(
            name='People',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='movieactor',
            name='actor',
            field=models.ForeignKey(to='movies.People'),
        ),
        migrations.AddField(
            model_name='movieactor',
            name='movie',
            field=models.ForeignKey(to='movies.Movie'),
        ),
        migrations.AddField(
            model_name='movie',
            name='director',
            field=models.ForeignKey(related_name='movies_directed', to='movies.People'),
        ),
        migrations.AddField(
            model_name='movie',
            name='distributor',
            field=models.ForeignKey(related_name='movies_distributed', to='movies.Company', null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='production_company',
            field=models.ForeignKey(related_name='movies_produced', to='movies.Company'),
        ),
        migrations.AddField(
            model_name='movie',
            name='writer',
            field=models.ForeignKey(related_name='movies_written', to='movies.People', null=True),
        ),
        migrations.AddField(
            model_name='geocodingcache',
            name='location',
            field=models.OneToOneField(to='movies.Location'),
        ),
    ]
