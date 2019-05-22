# -*- coding: utf-8 -*-
# admin显示控制
from django.contrib import admin

from models import (Application, BusinessInstanceStep,
                    BusinessInstanceStepDetail, BusinessRecord,
                    BusinessTemplate, BusinessTemplateStep,
                    BusinessTemplateStepDetail, BusinessType)


class BusinessTemplateAdmin(admin.ModelAdmin):
    search_fields = ('business_name', 'business_type')
    list_display = ('business_name', 'business_type')
    list_filter = ('business_type', )


class BusinessRecordAdmin(admin.ModelAdmin):
    search_fields = ['business_name', 'business_type', 'template_name', 'status', 'submit_status']
    list_display = ('template_name', 'business_name', 'business_type', 'status', 'submit_status')
    list_filter = ('business_type', 'status')


class BusinessTemplateStepAdmin(admin.ModelAdmin):
    search_fields = ('name', 'business_step')
    list_display = ('name', 'business_step')
    list_filter = ('business',)


class BusinessTemplateStepDetailAdmin(admin.ModelAdmin):
    search_fields = ('step_xh', 'business_step',)
    list_display = ('step_xh', 'business_step',)


class BusinessInstanceStepAdmin(admin.ModelAdmin):
    search_fields = ('name', 'business')
    list_display = ('name', 'business')
    list_filter = ('business',)


class BusinessInstanceStepDetailAdmin(admin.ModelAdmin):
    search_fields = ('step_xh', 'business_step')
    list_display = ('step_xh', 'business_step', 'stat', )
    list_filter = ('stat', )


admin.site.register(BusinessTemplate, BusinessTemplateAdmin)
admin.site.register(BusinessRecord, BusinessRecordAdmin)
admin.site.register(BusinessTemplateStep, BusinessTemplateStepAdmin)
admin.site.register(BusinessInstanceStep, BusinessInstanceStepAdmin)
admin.site.register(BusinessInstanceStepDetail, BusinessInstanceStepDetailAdmin)
admin.site.register(BusinessTemplateStepDetail, BusinessTemplateStepDetailAdmin)
admin.site.register(Application)
admin.site.register(BusinessType)
