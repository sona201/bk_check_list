# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('task_center', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessinstancestepdetail',
            name='responser',
            field=models.ManyToManyField(related_name='businessinstancestepdetail_responser', verbose_name='\u8d1f\u8d23\u4eba', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='businesstemplatestepdetail',
            name='responser',
            field=models.ManyToManyField(related_name='businesstemplatestepdetail_responser', verbose_name='\u8d1f\u8d23\u4eba', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
