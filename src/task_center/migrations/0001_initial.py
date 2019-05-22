# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cc_id', models.IntegerField(verbose_name='cc\u4e1a\u52a1\u7f16\u7801')),
                ('cc_name', models.CharField(unique=True, max_length=30, verbose_name='cc\u4e1a\u52a1\u540d')),
                ('cc_name_abbr', models.CharField(max_length=30, null=True, verbose_name='cc\u4e1a\u52a1\u540d\u7f29\u5199', blank=True)),
                ('operator', models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='\u4e1a\u52a1\u53ef\u64cd\u4f5c\u8005')),
            ],
            options={
                'verbose_name': '\u4e1a\u52a1\u540d\u79f0',
                'verbose_name_plural': '\u4e1a\u52a1\u540d\u79f0',
            },
        ),
        migrations.CreateModel(
            name='BusinessInstanceStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='\u6b65\u9aa4\u540d\u79f0')),
            ],
            options={
                'verbose_name': '\u4efb\u52a1\u5b9e\u4f8b\u6b65\u9aa4',
                'verbose_name_plural': '\u4efb\u52a1\u5b9e\u4f8b\u6b65\u9aa4',
            },
        ),
        migrations.CreateModel(
            name='BusinessInstanceStepDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('step_xh', models.IntegerField(verbose_name='\u6b65\u9aa4\u5e8f\u53f7')),
                ('operate_attention', models.TextField(verbose_name='\u64cd\u4f5c\u4e8b\u9879')),
                ('comment', models.TextField(verbose_name='\u5907\u6ce8')),
                ('importance', models.BooleanField(default=False, verbose_name='\u662f\u5426\u91cd\u8981')),
                ('stat', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u9ed8\u8ba4'), (1, '\u5220\u9664'), (2, '\u65b0\u589e'), (3, '\u7f16\u8f91')])),
                ('operation', models.IntegerField(default=0, blank=True, verbose_name='\u64cd\u4f5c', choices=[(0, '\u9ed8\u8ba4'), (1, '\u5b8c\u6210'), (2, '\u4e0d\u6d89\u53ca')])),
                ('confirm_info', models.TextField(null=True, blank=True)),
                ('done_time', models.DateTimeField(null=True, verbose_name='\u5b8c\u6210\u65f6\u95f4', blank=True)),
                ('business_step', models.ForeignKey(related_name='business_step', to='task_center.BusinessInstanceStep')),
                ('confirm_user', models.ForeignKey(related_name='confirm_user', verbose_name='\u786e\u8ba4\u4eba', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('responser', models.ManyToManyField(related_name='businessinstancestepdetail_responser', null=True, verbose_name='\u8d1f\u8d23\u4eba', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'verbose_name': '\u4efb\u52a1\u5b9e\u4f8b\u8be6\u7ec6\u4e8b\u9879',
                'verbose_name_plural': '\u4efb\u52a1\u5b9e\u4f8b\u8be6\u7ec6\u4e8b\u9879',
            },
        ),
        migrations.CreateModel(
            name='BusinessRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('business_name', models.CharField(max_length=100, verbose_name='\u4e1a\u52a1\u540d\u79f0')),
                ('template_name', models.CharField(max_length=100, verbose_name='\u6a21\u677f\u540d\u79f0')),
                ('business_type', models.CharField(max_length=20, verbose_name='\u4e1a\u52a1\u7c7b\u578b')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('business_name_order', models.CharField(max_length=100, verbose_name='\u6392\u5e8f\u7528\u4e1a\u52a1\u540d\u79f0')),
                ('business_version', models.CharField(db_index=True, max_length=50, null=True, verbose_name='\u64cd\u4f5c\u8bc6\u522b\u53f7', blank=True)),
                ('current_step', models.IntegerField(default=1, verbose_name='\u5f53\u524d\u64cd\u4f5c\u6b65\u9aa4')),
                ('status', models.IntegerField(verbose_name='\u5ba1\u6838\u7ed3\u679c', choices=[(0, '\u5f85\u5ba1\u6838'), (1, '\u5ba1\u6838\u901a\u8fc7'), (2, '\u9a73\u56de'), (3, '\u64cd\u4f5c\u4e2d'), (4, '\u5b8c\u6210'), (5, '\u5e9f\u5f03')])),
                ('audit_reason', models.TextField(null=True, verbose_name='\u5ba1\u6838\u539f\u56e0', blank=True)),
                ('submit_status', models.IntegerField(verbose_name='\u63d0\u4ea4\u72b6\u6001', choices=[(0, '\u672a\u63d0\u4ea4'), (1, '\u63d0\u4ea4')])),
                ('app', models.ForeignKey(verbose_name='\u4e1a\u52a1', to='task_center.Application')),
                ('audit_user', models.ManyToManyField(related_name='audit_user', verbose_name='\u5ba1\u6838\u4eba', to=settings.AUTH_USER_MODEL)),
                ('creator', models.ForeignKey(related_name='businessrecord_creator', verbose_name='\u521b\u5efa\u8005', to=settings.AUTH_USER_MODEL)),
                ('operator', models.ManyToManyField(related_name='businessrecord_operator', verbose_name='\u6a21\u677f\u53ef\u64cd\u4f5c\u8005', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u4efb\u52a1\u5b9e\u4f8b',
                'verbose_name_plural': '\u4efb\u52a1\u5b9e\u4f8b',
            },
        ),
        migrations.CreateModel(
            name='BusinessTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('business_name', models.CharField(max_length=100, verbose_name='\u4e1a\u52a1\u540d\u79f0')),
                ('template_name', models.CharField(max_length=100, verbose_name='\u6a21\u677f\u540d\u79f0')),
                ('business_type', models.CharField(max_length=20, verbose_name='\u4e1a\u52a1\u7c7b\u578b')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='\u6700\u540e\u66f4\u65b0\u65f6\u95f4', null=True)),
                ('app', models.ForeignKey(verbose_name='\u4e1a\u52a1', to='task_center.Application')),
                ('creator', models.ForeignKey(related_name='businesstemplate_creator', verbose_name='\u521b\u5efa\u8005', to=settings.AUTH_USER_MODEL)),
                ('operator', models.ManyToManyField(related_name='businesstemplate_operator', verbose_name='\u6a21\u677f\u53ef\u64cd\u4f5c\u8005', to=settings.AUTH_USER_MODEL)),
                ('updater', models.ForeignKey(related_name='updater', verbose_name='\u6700\u540e\u66f4\u65b0\u8005', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u4e1a\u52a1\u6a21\u677f',
                'verbose_name_plural': '\u4e1a\u52a1\u6a21\u677f',
            },
        ),
        migrations.CreateModel(
            name='BusinessTemplateStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='\u6b65\u9aa4\u540d\u79f0')),
                ('business', models.ForeignKey(related_name='business', to='task_center.BusinessTemplate')),
            ],
            options={
                'verbose_name': '\u4e1a\u52a1\u6a21\u7248\u6b65\u9aa4',
                'verbose_name_plural': '\u4e1a\u52a1\u6a21\u7248\u6b65\u9aa4',
            },
        ),
        migrations.CreateModel(
            name='BusinessTemplateStepDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('step_xh', models.IntegerField(verbose_name='\u6b65\u9aa4\u5e8f\u53f7')),
                ('operate_attention', models.TextField(verbose_name='\u64cd\u4f5c\u4e8b\u9879')),
                ('comment', models.TextField(verbose_name='\u5907\u6ce8')),
                ('importance', models.BooleanField(default=False, verbose_name='\u662f\u5426\u91cd\u8981')),
                ('business_step', models.ForeignKey(related_name='business_step', to='task_center.BusinessTemplateStep')),
                ('responser', models.ManyToManyField(related_name='businesstemplatestepdetail_responser', null=True, verbose_name='\u8d1f\u8d23\u4eba', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'verbose_name': '\u4e1a\u52a1\u6a21\u7248\u8be6\u7ec6\u4e8b\u9879',
                'verbose_name_plural': '\u4e1a\u52a1\u6a21\u7248\u8be6\u7ec6\u4e8b\u9879',
            },
        ),
        migrations.CreateModel(
            name='BusinessType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('types', models.CharField(max_length=100, verbose_name='\u6a21\u7248\u7c7b\u578b')),
                ('app', models.ForeignKey(to='task_center.Application')),
            ],
            options={
                'verbose_name': '\u6a21\u7248\u7c7b\u578b',
                'verbose_name_plural': '\u6a21\u7248\u7c7b\u578b',
            },
        ),
        migrations.AddField(
            model_name='businessinstancestep',
            name='business',
            field=models.ForeignKey(related_name='business', to='task_center.BusinessRecord'),
        ),
        migrations.AlterUniqueTogether(
            name='businesstemplatestep',
            unique_together=set([('name', 'business')]),
        ),
        migrations.AlterUniqueTogether(
            name='businesstemplate',
            unique_together=set([('business_name', 'template_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='businessrecord',
            unique_together=set([('business_name', 'template_name')]),
        ),
    ]
