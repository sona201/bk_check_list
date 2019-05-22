# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('task_center.views',
                       # 页面公共部分
                       url(r'^business_type/$', 'get_business_type'),
                       url(r'users/$', 'users'),
                       url(r'^business_name/$', 'get_business_name'),
                       # 模版&任务增删改查公共接口
                       url(r'^template/details/$', 'template_details'),
                       url(r'^template/step_delete/$', 'step_delete'),
                       url(r'^template/step_create/$', 'step_create'),
                       url(r'^template/step_change/$', 'step_change'),
                       url(r'^template/step_import/$', 'step_import'),
                       url(r'^template/query/$', 'template_query'),
                       # 业务配置部分
                       url(r'^app/$', 'app_manager'),
                       url(r'^app/all/$', 'application_query'),
                       url(r'^app/delete/$', 'application_delete'),
                       url(r'^app/change/$', 'application_change'),
                       url(r'^app/create/$', 'application_create'),
                       url(r'^app/type/$', 'application_type'),
                       url(r'^app/type_query/$', 'application_type_query'),
                       url(r'^app/type_create/$', 'application_type_create'),
                       url(r'^app/type_change/$', 'application_type_change'),
                       url(r'^app/type_delete/$', 'application_type_delete'),
                       # 模版配置部分
                       url(r'^edit/$', 'manage_edit'),
                       url(r'^app/type_create/$', 'application_type_create'),
                       url(r'^edit/operator_change/$', 'operator_change'),
                       url(r'^edit/operator_get/$', 'operator_get'),
                       url(r'^edit/template_download/$', 'template_download'),
                       url(r'^edit/responser_change/$', 'responser_change'),
                       url(r'^edit/file_import/$', 'file_import'),
                       url(r'^edit/template_save/$', 'template_save'),
                       url(r'^edit/template_create/$', 'template_create'),
                       url(r'^edit/template_delete/$', 'template_delete'),
                       url(r'^edit/template_change/$', 'template_change'),
                       # 创建任务部分
                       url(r'^task/business_create/$', 'business_create'),
                       url(r'^task/check_version/$', 'check_version'),
                       # 任务中心部分
                       url(r'^$', 'history'),
                       url(r'^history/business_query/$', 'business_query'),
                       url(r'^history/business_change/$', 'business_change'),
                       url(r'^history/status_set/$', 'status_set'),
                       url(r'^history/change_stat/$', 'change_stat'),
                       url(r'^history/business_operate/$', 'business_operate'),
                       url(r'^business/check_msg/$', 'check_msg'),
                       url(r'^business/save_actions/$', 'save_actions'),
                       url(r'^business/steps_status_get/$', 'steps_status_get'),
                       # 帮助文档
                       url(r'^help/$', 'help_document'),
                       )
