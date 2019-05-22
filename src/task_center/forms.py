# -*- coding: utf-8 -*-
import json
import re

from django import forms

from common.log import logger
from models import Application, BusinessType
from utils import check_value


def order_clean(order, collation, default):
    if order == 'details':
        order = default
    if collation == 'desc':
        order = '-' + order
    return order


def space_replace(string):
    return string.replace('&nbsp;', ' ').strip()


class ApplicationQueryForm(forms.Form):
    offset = forms.IntegerField(label=u"起始ID")
    length = forms.IntegerField(label=u"分页长度")
    collation = forms.ChoiceField(label=u"排序规则", choices=(('desc', ''), ('asc', '')))
    order = forms.CharField(label=u"排序字段", max_length=30)
    cc_name = forms.CharField(label=u"业务名称", max_length=100, required=False)
    cc_name_abbr = forms.CharField(label=u"业务名称缩写", max_length=100, required=False)
    operator = forms.CharField(label=u"业务可操作者", required=False)

    def clean_order(self):
        order = self.cleaned_data['order']
        collation = self.cleaned_data['collation']
        return order_clean(order, collation, 'cc_id')


class ApplicationTypeQueryForm(forms.Form):
    offset = forms.IntegerField(label=u"起始ID")
    length = forms.IntegerField(label=u"分页长度")
    collation = forms.ChoiceField(label=u"排序规则", choices=(('desc', ''), ('asc', '')))
    order = forms.CharField(label=u"排序字段", max_length=30)
    cc_name = forms.CharField(label=u"业务名称", max_length=100, required=False)
    template_type = forms.CharField(label=u"业务类型", max_length=100, required=False)

    def clean_cc_name(self):
        if self.cleaned_data['cc_name'] == 'all':
            return ''
        else:
            return self.cleaned_data['cc_name']

    def clean_collation(self):
        return self.cleaned_data['collation'] == 'desc'

    def clean_order(self):
        order = self.cleaned_data['order']
        collation = self.cleaned_data['collation']
        return order_clean(order, collation, 'pk')


class ApplicationInfoForm(forms.Form):
    pk = forms.IntegerField(label='ID', required=False)
    cc_id = forms.IntegerField(label='cc_id')
    cc_name = forms.CharField(label=u"业务名称", max_length=100)
    cc_name_abbr = forms.CharField(label=u"业务名称缩写", max_length=100, required=False)
    operator = forms.CharField(label=u"可操作者", required=False)

    def clean_cc_name(self):
        cc_name = self.cleaned_data['cc_name']
        pattern = re.compile(ur"^(?!_)(?!-)[\u4e00-\u9fa5A-Za-z0-9_-]+$")
        if cc_name == u"全部" or not pattern.match(cc_name):
            raise forms.ValidationError(u"业务名不合法")
        return cc_name

    def clean_cc_name_abbr(self):
        cc_name_abbr = self.cleaned_data['cc_name_abbr']
        if not cc_name_abbr:
            cc_name_abbr = None
            return cc_name_abbr
        pattern = re.compile(ur"^(?!_)(?!-)[\u4E00-\u9FA5A-Za-z0-9_-]+$")
        if not pattern.match(cc_name_abbr):
            raise forms.ValidationError(u"业务名缩写不合法")
        return cc_name_abbr


class ApplicationTypeForm(forms.Form):
    cc_name = forms.CharField(label=u"业务名称", max_length=100)
    template_type = forms.CharField(label=u"业务类型名称", max_length=100)

    def clean_template_type(self):
        template_type = self.cleaned_data['template_type']
        if not check_value(template_type, 'string')[0]:
            raise forms.ValidationError(u"模版类型名称不合法")
        return template_type


class ApplicationTypeChangeForm(forms.Form):
    template_type = forms.CharField(label=u"业务类型名称", max_length=100)
    pk = forms.IntegerField(label="id")

    def clean_template_type(self):
        template_type = self.cleaned_data['template_type']
        if not check_value(template_type, 'string')[0]:
            raise forms.ValidationError(u"模版类型名称不合法")
        return template_type


class BusinessQueryForm(forms.Form):
    business_type = forms.CharField(label=u"业务类型", max_length=100, required=False)
    business_name = forms.CharField(label=u"业务名称", max_length=100, required=False)
    business_version = forms.CharField(label=u"操作识别号", max_length=100, required=False)
    template_name = forms.CharField(label=u"模版名称", max_length=100, required=False)
    status = forms.CharField(label=u"任务状态", max_length=100, required=False)
    creator = forms.CharField(label=u"创建者", required=False)
    offset = forms.IntegerField(label=u"起始ID")
    length = forms.IntegerField(label=u"分页长度")
    collation = forms.ChoiceField(label=u"排序规则", choices=(('desc', ''), ('asc', '')))
    order = forms.CharField(label=u"排序字段", max_length=30)

    def clean_order(self):
        order = self.cleaned_data['order']
        collation = self.cleaned_data['collation']
        return order_clean(order, collation, 'create_time')


class OperatorChangeForm(forms.Form):
    operator = forms.CharField(label=u'可操作者')
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)


class ResponserChangeForm(forms.Form):
    responser = forms.CharField(label=u'责任人')
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)


class TemplateSaveForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    business_type = forms.CharField(label=u"模版类型", max_length=100)
    operator = forms.CharField(label=u'可操作者')
    template_data = forms.CharField(label=u"模版数据")

    def clean_businerss_name(self):
        business_name = self.cleaned_data['business_name']
        if not Application.objects.filter(c_name=business_name).exists():
            raise forms.ValidationError(u"业务名称不合法")
        return business_name

    def clean_template_name(self):
        template_name = self.cleaned_data['template_name']
        if not check_value(template_name, 'string')[0]:
            raise forms.ValidationError(u"模版名称不合法")
        return template_name

    def clean_business_type(self):
        business_type = self.cleaned_data['business_type']
        if not BusinessType.objects.filter(app__cc_name=self.cleaned_data['business_name'],
                                           types=business_type).exists():
            raise forms.ValidationError(u"模版类型不合法")
        return business_type

    def clean_operator(self):
        operator = self.cleaned_data['operator'][:-1] if self.cleaned_data['operator'][-1] == ';'\
            else self.cleaned_data['operator']
        if not check_value(operator, 'user')[0]:
            raise forms.ValidationError(u"可操作者不合法")
        operator = operator.split(';')
        if len(operator) != Application.objects.get(
                cc_name=self.cleaned_data['business_name']).operator.filter(username__in=operator).count():
            raise forms.ValidationError(u"可操作者不合法")
        return self.cleaned_data['operator']

    def clean_template_data(self):
        template_data = self.cleaned_data['template_data']
        try:
            template_data = json.loads(template_data)
        except Exception as e:
            raise forms.ValidationError(e)
        return template_data


class StepDeleteForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    step_xh = forms.IntegerField(label=u"步骤序号")
    instance_flag = forms.BooleanField(required=False, label=u"删除位置")


class StepForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    step_xh = forms.IntegerField(label=u"步骤序号")
    instance_flag = forms.BooleanField(required=False, label=u"删除位置")
    operate_attention = forms.CharField(label=u"操作事项")
    comment = forms.CharField(label=u"备注", required=False)
    responser = forms.CharField(label=u"负责人")

    def clean_operate_attention(self):
        operate_attention = space_replace(self.cleaned_data['operate_attention'])
        if not check_value(operate_attention, 'string')[0]:
            raise forms.ValidationError(u"操作事项包含不合法字符")
        return operate_attention

    def clean_comment(self):
        comment = space_replace(self.cleaned_data['comment'])
        if not check_value(comment, 'string')[0]:
            raise forms.ValidationError(u"备注包含不合法字符")
        return comment


class StepImportForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    step_xh = forms.IntegerField(label=u"步骤序号")
    instance_flag = forms.BooleanField(label=u"删除位置", required=False)
    importance = forms.ChoiceField(label=u"修改操作", choices=(('true', ''), ('false', '')))

    def clean_importance(self):
        return self.cleaned_data['importance'] == 'true'


class TemplateDetailsForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    flag = forms.ChoiceField(label=u"修改位置", required=False, choices=((0, 'edit'), (1, 'business'), (2, 'task')))
    h_flag = forms.ChoiceField(label=u"是否为任务查看任务实例", choices=((0, 'edit'), (1, 'business')), required=False)
    audit_flag = forms.ChoiceField(label=u"是否是审核页面", choices=((0, 'edit'), (1, 'business')), required=False)

    def clean_flag(self):
        if not self.cleaned_data['flag']:
            return ''
        return int(self.cleaned_data['flag'])


class TemplateQueryForm(forms.Form):
    business_type = forms.CharField(label=u"业务类型", max_length=100, required=False)
    business_name = forms.CharField(label=u"业务名称", max_length=100, required=False)
    template_name = forms.CharField(label=u"模版名称", max_length=100, required=False)
    offset = forms.IntegerField(label=u"起始ID")
    length = forms.IntegerField(label=u"分页长度")
    collation = forms.ChoiceField(label=u"排序规则", choices=(('desc', ''), ('asc', '')))
    order = forms.CharField(label=u"排序字段", max_length=30)

    def clean_order(self):
        order = self.cleaned_data['order']
        collation = self.cleaned_data['collation']
        return order_clean(order, collation, 'operator')


class BusinessCreateForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    version = forms.CharField(label=u"任务版本", max_length=100)
    audit_user = forms.CharField(label=u"审核人")

    def clean_version(self):
        version = self.cleaned_data['version']
        if not check_value(version, 'string')[0]:
            raise forms.ValidationError(u"任务包含不合法字符")
        return version


def clean_audit_user(self):
    audit_user = self.cleaned_data['audit_user'][:-1] if self.cleaned_data['audit_user'][-1] == ';' \
        else self.cleaned_data['audit_user']
    if not check_value(audit_user, 'user')[0]:
        raise forms.ValidationError(u"审核人不合法")
    audit_user = audit_user.split(';')
    if len(audit_user) != Application.objects.get(
            cc_name=self.cleaned_data['business_name']).operator.filter(username__in=audit_user).count():
        raise forms.ValidationError(u"审核人不合法")
    return self.cleaned_data['audit_user']


class CheckVersionForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    version = forms.CharField(label=u"任务版本", max_length=100)


class BusinessChangeForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    flag = forms.ChoiceField(label=u"修改位置", required=False, choices=((0, 'edit'), (1, 'business'), (2, 'task')))

    def clean_flag(self):
        if not self.cleaned_data['flag']:
            return ''
        return int(self.cleaned_data['flag'])


class StatusSetForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    status = forms.ChoiceField(label=u"任务状态", choices=((1, u"审核通过"), (2, u"审核驳回"), (5, u"废弃")))
    audit_reason = forms.CharField(label=u"审核原因")

    def clean_audit_reason(self):
        audit_reason = space_replace(self.cleaned_data['audit_reason'])
        if not check_value(audit_reason, 'string')[0]:
            raise forms.ValidationError(u"审核原因包含不合法字符")
        return audit_reason

    def clean_status(self):
        if not self.cleaned_data['status']:
            return ''
        return int(self.cleaned_data['status'])


class SaveActionForm(forms.Form):
    business_name = forms.CharField(label=u"业务名称", max_length=100)
    template_name = forms.CharField(label=u"模版名称", max_length=100)
    force_msg = forms.CharField(label=u"强制确认信息", required=False)
    operate = forms.CharField(label=u"确认信息")

    def clean_force_msg(self):
        force_msg = space_replace(self.cleaned_data['force_msg'])
        if not check_value(force_msg, 'string')[0]:
            raise forms.ValidationError(u"强制确认信息包含不合法字符")
        return force_msg

    def clean_operate(self):
        try:
            operate = json.loads(self.cleaned_data['operate'])
            if len(operate):
                return operate
            else:
                raise forms.ValidationError(u"确认信息不合法")
        except Exception as e:
            logger.info(u"json load error %s" % e)
            raise forms.ValidationError(u"确认信息不合法")
