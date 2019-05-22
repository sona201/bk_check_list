# -*- coding: utf-8 -*-
import datetime
import json
import time
from collections import deque, OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse

import xlrd
import xlwt
from common.log import logger
from common.mymako import render_json, render_mako_context
from constants import (BUSINESS_DETAIL_MODEL, BUSINESS_MODEL,
                       BUSINESS_STEP_MODEL, BusinessStatus, DetailOperation,
                       ExcelList, Flag, HeadList, Stat, SubmitStat)
from forms import (ApplicationInfoForm, ApplicationQueryForm,
                   ApplicationTypeChangeForm, ApplicationTypeForm,
                   ApplicationTypeQueryForm, BusinessChangeForm,
                   BusinessCreateForm, BusinessQueryForm, CheckVersionForm,
                   OperatorChangeForm, ResponserChangeForm, SaveActionForm,
                   StatusSetForm, StepDeleteForm, StepForm, StepImportForm,
                   TemplateDetailsForm, TemplateQueryForm, TemplateSaveForm)
from models import (Application, BusinessInstanceStep,
                    BusinessInstanceStepDetail, BusinessRecord,
                    BusinessTemplate, BusinessTemplateStep,
                    BusinessTemplateStepDetail, BusinessType)
from utils import (check_init, check_users_from_paas, check_value,
                   create_task_step, delete_task_step, get_all_users,
                   get_param_data_by_name, string_to_users,
                   update_task_step)
from validators import check_operate, check_perm
from xlwt.Formatting import Alignment
from xlwt.Style import XFStyle


def users(request):
    """
    人名选择器，获取当前注册用户
    """
    if not request.method == 'POST':
        return HttpResponse()
    q = request.POST.get('q', '')
    cc_name = request.POST.get('cc_name', '')
    if not cc_name:
        users_list = get_all_users(request.COOKIES['bk_token'])
        data_list = [{'id': user, 'text': user}for user in users_list if not q or q in user]
        return HttpResponse(json.dumps(data_list))
    try:
        user_list = Application.objects.get(
            cc_name=cc_name).operator.all().values('username').values_list('username', flat=True).distinct()
    except ObjectDoesNotExist:
        return render_json([])
    if not user_list:
        return HttpResponse([])
    data_list = [{'id': user, 'text': user} for user in user_list if not q or q in user]
    return HttpResponse(json.dumps(data_list))


def get_business_type(request):
    """
    获取业务类型列表
    """
    if not request.method == 'POST':
        return HttpResponse()
    cc_name = request.POST.get('cc_name', '')
    q = request.POST.get('q', '')
    filter_query = Q()
    if cc_name != u'全部':
        apps = Application.objects.filter(cc_name=cc_name, operator__username=request.user.username)
    else:
        apps = Application.objects.filter(operator__username=request.user.username)
    if q:
        filter_query.add(Q(types__icontains=q), filter_query.AND)
    type_list = BusinessType.objects.filter(filter_query, app__in=apps).values('types').distinct()
    data_list = [{'id': types['types'], 'text': types['types']} for types in type_list]
    data_list.insert(0, {'id': 'all', 'text': u'全部'})
    return HttpResponse(json.dumps(data_list))


def get_business_name(request):
    """
    获取业务名称
    """
    if not request.method == 'POST':
        return HttpResponse()
    is_staff = request.POST.get('is_staff', '')
    if is_staff == '1':
        user = request.user
        if not user.is_staff:
            return HttpResponse([])
        else:
            apps = Application.objects.all().values('cc_name')
    else:
        filter_query = Q()
        filter_query.add(Q(operator__username=request.user.username), filter_query.AND)
        q = request.POST.get('q', '')
        if q:
            filter_query.add(Q(cc_name__icontains=q), filter_query.AND)
        apps = Application.objects.filter(filter_query).values('cc_name')
    data_list = [{'id': app['cc_name'], 'text': app['cc_name']} for app in apps]
    data_list.insert(0, {'id': 'all', 'text': u'全部'})
    return HttpResponse(json.dumps(data_list))


def template_details(request):
    """
    查看指定的业务模板
    """
    form = TemplateDetailsForm(request.GET)
    if not form.is_valid():
        return render_mako_context(request, '/manager/403.html', {'result': True, 'isNotPass': True,
                                                                  'data': u"参数错误，请修改重试"})
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']
    flag = form.cleaned_data['flag']
    h_flag = form.cleaned_data['h_flag']
    audit_flag = form.cleaned_data['audit_flag']
    if h_flag or audit_flag or flag == int(Flag.BUSINESS):
        cc_name = business_name.split('_')[0]
        business = BUSINESS_MODEL["instance"]
        business_flag = "instance"
    else:
        cc_name = business_name
        business = BUSINESS_MODEL["template"]
        business_flag = "template"
    try:
        Application.objects.get(cc_name=cc_name, operator__username=request.user.username)
        record = business.objects.get(business_name=business_name, template_name=template_name)
        parm_data = get_param_data_by_name(business_flag, business_name, template_name)
    except Exception, e:
        logger.error(u"查看失败,business_name:%s, template_name:%s, %s" % (business_name, template_name, e))
        return render_mako_context(request, '/manager/403.html', {'result': True, 'isNotPass': True,
                                                                  'data': u"查看失败，请重试！"})
    rec = business.to_dict(record)
    return render_mako_context(request, '/task_center/some_template_query.html',
                               {'parm_info': parm_data, 'template_name': template_name,
                                'template': rec, 'flag': flag, 'audit_flag': audit_flag, "active": False,
                                'h_flag': h_flag
                                })


@check_operate()
def step_delete(request):
    """
    删除指定步骤类别的步骤序号数据
    """
    form = StepDeleteForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'msg': u"参数错误"})
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']
    step_xh = form.cleaned_data['step_xh']
    # 删除模版or任务
    instance_flag = form.cleaned_data['instance_flag']
    if instance_flag:
        flag = delete_task_step("instance", business_name, template_name, step_xh, request.user.username)
    else:
        flag = delete_task_step("template", business_name, template_name, step_xh, request.user.username)
    if flag:
        return render_json({'result': flag, 'msg': u"删除步骤序号%s数据成功！" % step_xh})
    return render_json({'result': flag, 'msg': u"删除步骤%s失败！" % step_xh})


@check_operate()
@transaction.atomic()
def step_create(request):
    """
    @运维配置——编辑业务模板,新增指定位置步骤
    """
    form = StepForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'msg': u"参数错误"})
    b_name = form.cleaned_data['business_name']
    t_name = form.cleaned_data['template_name']
    step_xh = form.cleaned_data['step_xh']
    operate_attention = form.cleaned_data['operate_attention']
    comment = form.cleaned_data['comment']
    responser = form.cleaned_data['responser']
    instance_flag = form.cleaned_data['instance_flag']
    if not check_users_from_paas(responser, request.COOKIES['bk_token'])[0]:
        return render_json({'result': False, 'msg': u'参数不合法!'})
    if instance_flag:
        business = BUSINESS_MODEL['instance']
    else:
        business = BUSINESS_MODEL['template']
    try:
        business.objects.get(business_name=b_name, template_name=t_name)
    except ObjectDoesNotExist:
        logger.error(u'查询任务实例步骤失败，business_name: %s, template_name: %s, step_xh:%s' % (b_name, t_name, step_xh))
        return render_json({'result': False, 'msg': u"任务实例不存在"})

    if instance_flag:
        status = create_task_step("instance", b_name, t_name, step_xh, request.user.username, operate_attention,
                                  comment, responser)
    else:
        status = create_task_step("template", b_name, t_name, step_xh, request.user.username, operate_attention,
                                  comment, responser)
    if not status:
        return render_json({'result': False, 'msg': u"添加步骤 %s数据时失败" % step_xh})
    else:
        return render_json({'result': True, 'msg': u"添加步骤%s成功" % step_xh})


@check_operate()
@transaction.atomic()
def step_change(request):
    """
    编辑指定步骤类别的步骤序号的数据
    """
    form = StepForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'msg': u"参数不合法"})
    b_name = form.cleaned_data['business_name']
    t_name = form.cleaned_data['template_name']
    step_xh = form.cleaned_data['step_xh']
    operate_attention = form.cleaned_data['operate_attention']
    comment = form.cleaned_data['comment']
    responser = form.cleaned_data['responser']
    instance_flag = form.cleaned_data['instance_flag']
    if not check_users_from_paas(responser, request.COOKIES['bk_token'])[0]:
        return render_json({'result': False, 'msg': u'参数不合法!'})
    if instance_flag:
        status = update_task_step("instance", b_name, t_name, step_xh, request.user.username, operate_attention,
                                  comment, responser)
    else:
        status = update_task_step("template", b_name, t_name, step_xh, request.user.username, operate_attention,
                                  comment, responser)
    if not status:
        return render_json({'result': False, 'msg': u"修改步骤 %s失败" % step_xh})
    else:
        return render_json({'result': True, 'msg': u"修改步骤%s成功" % step_xh})


@check_operate()
@transaction.atomic()
def step_import(request):
    """
    标识操作步骤序列中的重要步骤项
    """
    form = StepImportForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False})
    b_name = form.cleaned_data['business_name']
    t_name = form.cleaned_data['template_name']
    step_xh = form.cleaned_data['step_xh']
    importance = form.cleaned_data['importance']
    instance_flag = form.cleaned_data['instance_flag']
    q = Q()
    if instance_flag:
        q = ~Q(stat=1)
        business_detail = BUSINESS_DETAIL_MODEL["instance"]
    else:
        business_detail = BUSINESS_DETAIL_MODEL["template"]
    business_detail.objects.filter(
        q,
        step_xh=step_xh,
        business_step__business__business_name=b_name,
        business_step__business__template_name=t_name,
        business_step__business__operator__username=request.user.username,
    ).update(importance=importance)
    return render_json({'result': True})


def template_query(request):
    """
    编辑业务模板——获取业务模板列表
    """
    forms = TemplateQueryForm(request.GET)
    if not forms.is_valid():
        return render_json({'result': False, 'data': [],  'total_count': 0})
    record_num = forms.cleaned_data['length']
    start = forms.cleaned_data['offset']
    business_type = forms.cleaned_data['business_type']
    business_name = forms.cleaned_data['business_name']
    template_name = forms.cleaned_data['template_name']
    order = forms.cleaned_data['order']
    username = request.user.username

    businesses = BusinessTemplate.objects.query(username, business_name, business_type, template_name, order)
    total = businesses.count()
    end = start + record_num
    businesses = businesses[start:end]
    data_list = []
    for business in businesses:
        business_dict = BusinessTemplate.to_dict(business)
        business_dict.update({'details': BusinessTemplate.to_dict(business)})
        data_list.append(business_dict)
    return render_json({'result': True, 'data': data_list, 'total_count': total})


@check_perm()
def app_manager(request):
    check_init(request.user.username)
    return render_mako_context(request, "/task_center/app.html", {})


@check_perm()
def application_query(request):
    """
    获取全部业务信息
    """
    forms = ApplicationQueryForm(request.GET)
    if not forms.is_valid():
        return render_json({'data': [], 'total_count': 0})
    start = forms.cleaned_data['offset']
    pagesize = forms.cleaned_data['length']
    cc_name = forms.cleaned_data['cc_name']
    cc_name_abbr = forms.cleaned_data['cc_name_abbr']
    operator = forms.cleaned_data['operator']
    order = forms.cleaned_data['order']

    apps = Application.objects.query(cc_name, cc_name_abbr, operator, order)
    total = apps.count()
    end = start + pagesize
    apps = apps[start: end]
    data_list = []
    for i in apps:
        details = Application.to_dict(i)
        details.update({'details': Application.to_dict(i)})
        data_list.append(details)
    return render_json({'data': data_list, 'total_count': total})


@check_perm()
def application_delete(request):
    """
    删除业务信息
    """
    pk = request.POST.get('pk', '')
    try:
        Application.objects.get(pk=pk).delete()
    except Exception, e:
        logger.info(u"删除业务失败，error: %s, pk:%s" % (e, pk))
        return render_json({'result': False, 'msg': u"删除业务失败！"})
    return render_json({'result': True, 'msg': u"删除业务成功！"})


@check_perm()
def application_change(request):
    """
    修改业务信息
    """
    forms = ApplicationInfoForm(request.POST)
    if not forms.is_valid():
        return render_json({'result': False, 'msg': u'参数不合法!'})
    pk = forms.cleaned_data['pk']
    if pk is None:
        return render_json({'result': False, 'msg': u'参数不合法!'})
    cc_name = forms.cleaned_data['cc_name']
    cc_name_abbr = forms.cleaned_data['cc_name_abbr']
    operator = forms.cleaned_data['operator']
    if not check_users_from_paas(operator, request.COOKIES['bk_token'])[0]:
        return render_json({'result': False, 'msg': u'参数不合法!'})
    n = Application.objects.filter(~Q(pk=pk), cc_name=cc_name).count()
    if n > 0:
        return render_json({'result': False, 'msg': u'业务名已存在，请修改重试!'})
    try:
        app = Application.objects.get(pk=pk)
        app.cc_name = cc_name
        app.cc_name_abbr = cc_name_abbr
        operators = string_to_users(operator)
        app.operator.clear()
        for operator in operators:
            app.operator.add(operator)
        app.save()
    except ObjectDoesNotExist:
        return render_json({'result': False, 'msg': u'修改业务失败!'})
    return render_json({'result': True, 'msg': u'修改业务成功!'})


@check_perm()
def application_create(request):
    """
    增加业务
    """
    form = ApplicationInfoForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'msg': u'参数不合法!'})
    cc_id = form.cleaned_data['cc_id']
    cc_name = form.cleaned_data['cc_name']
    cc_name_abbr = form.cleaned_data['cc_name_abbr']
    operator = form.cleaned_data['operator']
    if not check_users_from_paas(operator, request.COOKIES['bk_token'])[0]:
        return render_json({'result': False, 'msg': u'参数不合法!'})
    n = Application.objects.filter(cc_id=cc_id).count()
    if n > 0:
        return render_json({'result': False, 'msg': u"该业务编码已存在，请修改重试！"})
    n = Application.objects.filter(cc_name=cc_name).count()
    if n > 0:
        return render_json({'result': False, 'msg': u"该业务名称已存在，请修改重试！"})
    try:
        app = Application.objects.create(cc_name=cc_name,
                                         cc_name_abbr=cc_name_abbr,
                                         cc_id=cc_id)
        operator = string_to_users(operator)
        for i in operator:
            app.operator.add(i)
        app.save()
    except Exception, e:
        logger.error(u"增加业务失败%s" % e)
        return render_json({'result': False, 'msg': u"添加业务失败！"})
    return render_json({'result': True, 'msg': u"添加业务成功！"})


def application_type(request):
    check_init(request.user.username)
    return render_mako_context(request, '/task_center/app_type.html')


@check_perm()
def application_type_query(request):
    form = ApplicationTypeQueryForm(request.GET)
    if not form.is_valid():
        return render_json({'data': [], 'total_count': 0})

    cc_name = form.cleaned_data['cc_name']
    template_type = form.cleaned_data['template_type']
    start = form.cleaned_data['offset']
    pagesize = form.cleaned_data['length']
    order = form.cleaned_data['order']
    collation = form.cleaned_data['collation']
    q = Q()
    if cc_name:
        q.add(Q(app__cc_name=cc_name), q.AND)
    if template_type:
        q.add(Q(types__icontains=template_type), q.AND)
    type_list = BusinessType.objects.filter(q)
    total = type_list.count()
    end = start + pagesize
    type_lists = BusinessType.to_dict(type_list)
    type_lists = sorted(type_lists, key=lambda k: k[order], reverse=collation)[start: end]
    return render_json({'data': type_lists, 'total_count': total})


@check_perm()
def application_type_create(request):
    form = ApplicationTypeForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, "msg": u'参数错误！'})
    cc_name = form.cleaned_data['cc_name']
    template_type = form.cleaned_data['template_type']
    try:
        app = Application.objects.get(cc_name=cc_name)
    except ObjectDoesNotExist:
        return render_json({'result': False, "msg": u'业务名称错误！'})
    n = BusinessType.objects.filter(app=app, types=template_type).count()
    if n > 0:
        return render_json({'result': False, "msg": u'模版类型已存在！'})
    else:
        try:
            BusinessType.objects.create(types=template_type, app=app)
            return render_json({'result': True, "msg": u'增加模版类型成功！'})
        except Exception, e:
            logger.error(u'增加模版类型错误， %s！' % e)
            return render_json({'result': False, "msg": u'增加模版类型错误！'})


@check_perm()
def application_type_change(request):
    form = ApplicationTypeChangeForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, "msg": u'参数错误！'})
    pk = form.cleaned_data['pk']
    template_type = form.cleaned_data['template_type']
    try:
        type_ = BusinessType.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return render_json({'result': False, "msg": u'参数错误！'})
    if BusinessType.objects.filter(~Q(pk=pk), types=template_type, app=type_.app).exists():
        return render_json({'result': False, "msg": u'模版类型已存在！'})
    type_.types = template_type
    type_.save()
    return render_json({'result': True, "msg": u'修改模版类型成功！'})


@check_perm()
def application_type_delete(request):
    pk = request.POST.get('id', '')
    try:
        BusinessType.objects.get(pk=pk).delete()
        return render_json({'result': True, "msg": u'删除模版类型成功！'})
    except ObjectDoesNotExist:
        return render_json({'result': False, "msg": u'删除模版类型失败！'})


def manage_edit(request):
    """
    模版配置
    """
    check_init(request.user.username)
    return render_mako_context(request, '/task_center/template_edit.html', {})


def template_create(request):
    """
    新建模版页面
    """
    check_init(request.user.username)
    return render_mako_context(request, '/task_center/new_template.html')


def template_delete(request):
    """
    @编辑业务模板——删除指定的业务模板
    """
    pk = request.POST.get('pk', '')
    try:
        template = BusinessTemplate.objects.get(id=pk, operator__username=request.user.username)
    except ObjectDoesNotExist:
        return render_json({'result': False, 'message': u"权限不足！"})
    try:
        template.delete()
    except Exception, e:
        logger.error(u'删除pk为%s的业务模板失败，%s' % (pk, e))
        return render_json({'result': False, 'message': u'删除该业务模板失败'})
    return render_json({'result': True, 'message': u'删除该业务模板成功'})


@check_operate()
def template_change(request):
    """
    @编辑业务模板——编辑指定的业务模板
    """
    b_name = request.GET.get('business_name', '')
    t_name = request.GET.get('template_name', '')
    try:
        template = BusinessTemplate.objects.get(business_name=b_name, template_name=t_name)
        parm_data = get_param_data_by_name(types='template', b_name=b_name, t_name=t_name)
        rec = BusinessTemplate.to_dict(template)
        return render_mako_context(request, '/task_center/some_template_edit.html',
                                   {'template': rec, 'parm_data': parm_data, 'flag': 0,
                                    "active": True})
    except ObjectDoesNotExist:
        logger.warning(u"BusinessTemplate.DoesNotExist ,business_name=%s,template_name=%s" % (b_name, t_name))
        return HttpResponse(u"模板不存在,请重试！")
    except Exception, e:
        logger.error(u"get BusinessTemplate error,business_name=%s,template_name=%s,msg:%s" % (b_name, t_name, e))
        return HttpResponse(u"获取" + b_name + u"模板信息失败,请重试！")


def operator_get(request):
    template_name = request.POST.get('template_name', '')
    business_name = request.POST.get('business_name', '')
    try:
        template = BusinessTemplate.objects.get(
            template_name=template_name, business_name=business_name, operator__username=request.user.username)
        return render_json({'result': True, 'data': BusinessTemplate.get_operator(template)})
    except ObjectDoesNotExist:
        return render_json({'result': False, 'data': ''})


def operator_change(request):
    """
    更新模板可操作者
    """
    form = OperatorChangeForm(request.POST)
    if not form.is_valid():
        return render_json({'status': False, 'msg': u"数据不合法！"})
    operator = form.cleaned_data['operator']
    if not check_users_from_paas(operator, request.COOKIES['bk_token'])[0]:
        return render_json({'status': False, 'msg': u'部分可操作者不存在!'})

    template_name = form.cleaned_data['template_name']
    business_name = form.cleaned_data['business_name']

    username = request.user.username
    try:
        template = BusinessTemplate.objects.get(
            business_name=business_name, template_name=template_name, operator__username=username)
    except ObjectDoesNotExist:
        return render_json({'status': False, 'msg': u"权限不足！"})
    try:
        cc_name = template.business_name
        operator_list = string_to_users(operator)
        if operator_list.count() != Application.objects.get(
                cc_name=cc_name).operator.filter(username__in=operator.split(';')).count():
            return render_json({'status': False, 'msg': u"部分可操作者无该app权限！"})
        template.updater = request.user
        template.update_time = datetime.datetime.now()
        template.operator.clear()
        for i in operator_list:
            template.operator.add(i)
        template.save()
    except Exception, e:
        logger.error(u'更新纪录失败，%s; updater: %s, operator: %s pk:%s' % (e, username, operator, template.pk))
        return render_json({'status': False, 'msg': u"更新纪录失败！"})
    return render_json({'result': True, 'msg': u"更新纪录成功！"})


def template_download(request):
    """
    导出模板数据到excel
    """
    pk = request.GET.get('pk', '')
    business_name = request.GET.get('business_name', '')
    template_name = request.GET.get('template_name', '')
    flag = request.GET.get('flag', '')
    res_json = {
        'result': True,
        'isNotPass': True,
        'data': u""
    }
    if pk or flag == Flag.EDIT or flag == Flag.TASK or flag == 'False':
        business = BUSINESS_MODEL['template']
        cc_name = business_name
    elif flag == Flag.BUSINESS:
        business = BUSINESS_MODEL['instance']
        cc_name = business_name.split('_')[0]
    else:
        res_json['data'] = u'参数错误'
        return render_mako_context(request, '/manager/403.html', res_json)

    # 获取对应的模版并校验权限
    try:
        if pk:
            template = business.objects.get(id=pk)
            Application.objects.get(cc_name=template.business_name,
                                    operator__username=request.user.username)
        else:
            template = business.objects.get(business_name=business_name, template_name=template_name)
            Application.objects.get(cc_name=cc_name,
                                    operator__username=request.user.username)
    except ObjectDoesNotExist:
        res_json['data'] = u'您无操作权限,请联系系统管理员'
        return render_mako_context(request, '/manager/403.html', res_json)

    # 表格初始化
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response['Content-Disposition'] = 'attachment; filename="%s_%s.xls"' % (
        template.business_name.encode('utf-8'), template.business_type.encode('utf-8'))
    wbk = xlwt.Workbook(encoding='utf-8')
    sheet = wbk.add_sheet('sheet1')
    sheet.col(2).width = 20000
    sheet.col(3).width = 20000

    # 枚举参数初始化
    if flag == Flag.EDIT or flag == Flag.TASK or flag == 'False':
        head_list = HeadList.TEMPLATE
        excel_list = ExcelList.TEMPLATE
        business_step = BUSINESS_STEP_MODEL["template"]
        business_detail = BUSINESS_DETAIL_MODEL['template']
        q = Q()
    else:
        q = ~Q(stat=1)
        head_list = HeadList.INSTANCE
        excel_list = ExcelList.INSTANCE
        business_step = BUSINESS_STEP_MODEL['instance']
        business_detail = BUSINESS_DETAIL_MODEL['instance']
    try:
        for i, data in enumerate(head_list):
            sheet.write(0, i, data)
        row = 1
        algn_center_hv = Alignment()
        algn_center_hv.horz = Alignment.HORZ_CENTER
        algn_center_hv.vert = Alignment.VERT_CENTER
        style_cdata = XFStyle()
        style_cdata.alignment = algn_center_hv

        # 获取步骤详情并填充表格
        steps = business_step.objects.filter(business=template).order_by('id')
        for step in steps:
            details = business_detail.objects.filter(
                q, business_step=step).order_by('step_xh')
            sheet.write_merge(row, row + details.count() - 1, 0, 0, step.name, style_cdata)
            details = business_detail.to_dict(details)
            for detail in details:
                for i, value_key in enumerate(excel_list):
                    sheet.write(row, i + 1, detail[value_key])
                row += 1
        wbk.save(response)
        return response
    except Exception, e:
        logger.error(u'下载模版失败%s' % e)
        res_json['data'] = u'下载模版失败'
        return render_mako_context(request, '/manager/403.html', res_json)


@check_operate()
def responser_change(request):
    """
    模板编辑中批量修改责任人
    """
    form = ResponserChangeForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, "msg": u'参数错误！'})
    responser = form.cleaned_data['responser']
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']
    if not check_users_from_paas(responser, request.COOKIES['bk_token'])[0]:
        return render_json({'result': False, 'msg': u'参数不合法!'})
    responser = string_to_users(responser)
    try:
        details = BusinessTemplateStepDetail.objects.filter(
            business_step__business__business_name=business_name,
            business_step__business__template_name=template_name,
        )
        for detail in details:
            detail.responser.clear()
            for i in responser:
                detail.responser.add(i)
            detail.save()
    except Exception, e:
        logger.error(u'修改责任人失败，ERROR %s, business_name: %s, template_name: %s'
                     % (e, business_name, template_name))
        return render_json({'result': False, "msg": u'批量修改责任人失败，请联系管理员！'})
    return render_json({'result': True, "msg": u'批量修改责任人成功！'})


def file_import(request):
    """
    导入模板文件
    """
    files = request.FILES.get("file_data")
    try:
        data = xlrd.open_workbook(file_contents=files.read())
    except Exception, e:
        logger.error(u'导入数据失败%s' % e)
        return render_json({'success': False, 'message': u'非常抱歉，上传模版失败'})
    table = data.sheet_by_index(0)
    nrows = table.nrows
    parm_data = []
    merge = []

    try:
        step = ''
        step_num = 0
        rol = 0
        queue = deque([0])
        for i in range(1, nrows):
            if table.row(i)[0].value:
                step = table.row(i)[0].value
                if step_num != 0:
                    merge.append({
                        "row": queue.popleft(), "col": 0, "rowspan": step_num, "colspan": 1
                    })
                    queue.append(rol)
                step_num = 0
            if not check_value(table.row(i)[4].value.replace(' ', ''), 'user')[0]:
                return render_json({'success': False, 'message': u'模板【责任人】部分用户不存在，请检查!'})
            if not check_value(step + table.row(i)[2].value + table.row(i)[3].value + table.row(i)[4].value,
                               "string")[0]:
                return render_json({'success': False, 'message': u'模板包含非法字符，请检查!'})
            rol += 1
            step_num += 1
            parm_data.append({
                'step': step,
                'id': rol,
                'operate_attention': table.row(i)[2].value,
                'comment': table.row(i)[3].value,
                'responser': table.row(i)[4].value,
            })
        merge.append({
            "row": queue.popleft(), "col": 0, "rowspan": step_num, "colspan": 1
        })
    except Exception, e:
        logger.warning(u"导入模版失败%s", e)
        return HttpResponse(json.dumps({'success': False, "message": u'上传模版失败, 请检查！'}))
    return HttpResponse(json.dumps({'success': True, "message": parm_data, "merge": merge}))


def template_save(request):
    """
    保存模板
    """
    form = TemplateSaveForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'message': u'参数错误， 请修改重试！'})

    business_name = form.cleaned_data['business_name']
    operator = form.cleaned_data['operator']
    business_type = form.cleaned_data['business_type']
    template_data = form.cleaned_data['template_data']
    template_name = form.cleaned_data['template_name']
    user = request.user

    if BusinessTemplate.objects.filter(business_name=business_name, template_name=template_name).exists():
        return render_json({'result': False, 'message': u'模板名已经存在'})

    # 保存模版
    try:
        app = Application.objects.get(cc_name=business_name, operator__username=request.user.username)
    except ObjectDoesNotExist:
        return render_json({'result': False, 'message': u'无该业务权限'})
    with transaction.atomic():
        default = {'template_name': template_name, 'business_name': business_name, 'business_type': business_type,
                   'creator': user, 'updater': user, 'app': app}
        template = BusinessTemplate(**default)
        operator_list = string_to_users(operator)
        template.save()
        for i in operator_list:
            template.operator.add(i)
        template.save()

        # 保存步骤
        param = OrderedDict()
        # 步骤序号
        indexs = 1
        for one_data in template_data:
            step = one_data["step"]
            del one_data["step"], one_data["id"]
            one_data[u"step_xh"] = indexs
            if step not in param:
                param[step] = list()
            param[step].append(one_data)
            indexs += 1
        for keys in param:
            k = param[keys]
            tempstep = BusinessTemplateStep.objects.create(name=keys, business=template)

            # 保存详情
            for details in k:
                responser_list = string_to_users(details['responser'])
                del details['responser']
                detail = BusinessTemplateStepDetail(business_step=tempstep, **details)
                detail.save()
                for responser in responser_list:
                    detail.responser.add(responser)
                detail.save()
    return render_json({'result': True, 'message': u'恭喜你，导入数据成功！'})


@check_operate()
def business_create(request):
    """
    创建任务实例
    """
    form = BusinessCreateForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'msg': u"参数错误，请修改重试"})
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']
    version = form.cleaned_data['version']
    audit_user = form.cleaned_data['audit_user']
    name = '%s_%s' % (business_name, version)
    try:
        template = BusinessTemplate.objects.get(business_name=business_name, template_name=template_name)
    except ObjectDoesNotExist:
        return render_json({'result': False, 'msg': u"模版不存在", 'name': name, 'template_name': template_name})

    if BusinessRecord.objects.filter(business_name=name, business_type=template.business_type,
                                     template_name=template_name, business_version=version).exists():
        return render_json({
            'result': False, 'msg': u"启动该任务实例已存在。", 'name': name, 'template_name': template_name})
    with transaction.atomic():
        record = BusinessRecord.objects.create(business_name=name,
                                               business_name_order=business_name,
                                               template_name=template_name,
                                               business_type=template.business_type,
                                               business_version=version,
                                               create_time=datetime.datetime.now(),
                                               status='0',
                                               creator=request.user,
                                               submit_status='0',
                                               app=template.app
                                               )
        audit_user_list = string_to_users(audit_user)
        for audit_user in audit_user_list:
            record.audit_user.add(audit_user)
        operator_list = template.operator.all()
        for operator in operator_list:
            record.operator.add(operator)
        record.save()

        steps = BusinessTemplateStep.objects.filter(business=template)
        for step in steps:
            instance_step = BusinessInstanceStep.objects.create(name=step.name, business=record)
            details = BusinessTemplateStepDetail.objects.filter(business_step=step)
            for detail in details:
                business_detail = BusinessInstanceStepDetail.objects.create(step_xh=detail.step_xh,
                                                                            operate_attention=detail.operate_attention,
                                                                            comment=detail.comment,
                                                                            importance=detail.importance,
                                                                            business_step=instance_step
                                                                            )
                for responser in detail.responser.all():
                    business_detail.responser.add(responser)
                business_detail.save()
        return render_json({
            'result': True, 'msg': u"恭喜你，启动任务实例信息成功！", 'name': name, 'template_name': template_name})


@check_operate()
def check_version(request):
    """
    创建任务时，检查任务实例是否已经存在
    """
    form = CheckVersionForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False})
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']
    version = form.cleaned_data['version']
    name = '%s_%s' % (business_name, version)
    if not BusinessRecord.objects.filter(business_name=name, template_name=template_name,
                                         business_version=version).exists():
        return render_json({'result': True})
    return render_json({'result': False})


def history(request):
    """
    任务中心
    """
    check_init(request.user.username)
    return render_mako_context(request, '/task_center/history.html', {})


def business_query(request):
    """
    任务中心页面获取任务列表
    """
    forms = BusinessQueryForm(request.GET)
    if not forms.is_valid():
        return render_json({'data': [], 'total_count': 0})
    record_num = forms.cleaned_data['length']
    start = forms.cleaned_data['offset']
    business_type = forms.cleaned_data['business_type']
    business_name = forms.cleaned_data['business_name']
    business_version = forms.cleaned_data['business_version']
    template_name = forms.cleaned_data['template_name']
    status = forms.cleaned_data['status']
    creator = forms.cleaned_data['creator']
    order = forms.cleaned_data['order']
    username = request.user.username
    businesses = BusinessRecord.objects.query(
        username, business_name, business_type, business_version, template_name, status, order)
    if creator:
        q_f = Q()
        q_f.add(Q(creator__username__in=creator.split(';')), q_f.AND)
        businesses = businesses.filter(q_f)
    total = businesses.count()
    end = start + record_num
    businesses = businesses[start:end]
    data_list = []
    for business in businesses:
        detail = BusinessRecord.to_dict(business)
        detail.update({'details': BusinessRecord.to_dict(business)})
        data_list.append(detail)
    return render_json({'data': data_list, 'total_count': total})


@check_operate()
def business_change(request):
    """
   修改指定任务实例的详细步骤
    """
    form = BusinessChangeForm(request.GET)
    if not form.is_valid():
        return render_mako_context(request, '/manager/403.html', {'result': True, 'isNotPass': True,
                                                                  'data': u"参数错误，请修改重试"})
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']
    flag = form.cleaned_data['flag']
    try:
        record = BusinessRecord.objects.get(business_name=business_name, template_name=template_name)
    except ObjectDoesNotExist:
        return render_mako_context(request, '/manager/403.html', {'result': True, 'isNotPass': True,
                                                                  'data': u"参数错误，请修改重试"})
    try:
        parm_info = get_param_data_by_name("instance", b_name=business_name, t_name=template_name)
        if (record.status == BusinessStatus.WAITING or record.status == BusinessStatus.FAILED) \
                and record.submit_status == SubmitStat.DEFAULT:
            dic = BusinessRecord.to_dict(record)
            json_ = {'template': dic, 'parm_data': parm_info, 'status': record.status, 'audit_user': dic['audit_user'],
                     'flag': flag}
            return render_mako_context(request, '/task_center/edit_task_instance.html', json_)
        else:
            return HttpResponse(u"实例已提交，无法修改")
    except Exception as e:
        logger.error("business_change %s" % e)
        return render_mako_context(request, '/manager/403.html', {'result': True, 'isNotPass': True,
                                                                  'data': u"参数错误，请修改重试"})


def status_set(request):
    """
    设置业务模板的状态
    """
    form = StatusSetForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'msg': u"参数出错！"})
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']
    status = form.cleaned_data['status']
    audit_reason = form.cleaned_data['audit_reason']
    try:
        record = BusinessRecord.objects.get(business_name=business_name, template_name=template_name)
    except ObjectDoesNotExist:
        return render_json({'result': False, 'msg': u"模版不存在！"})
    user = request.user
    if user not in record.audit_user.all() and status in (BusinessStatus.SUCCESS, BusinessStatus.FAILED) \
            or user not in record.operator.all() and status in (
                    BusinessStatus.WAITING, BusinessStatus.SCRAP):
        return render_json({'result': False, 'msg': u"权限不足！"})
    if record.status in (BusinessStatus.SCRAP, BusinessStatus.OPERATING):
        return render_json({'result': False, 'msg': u"设置任务状态失败！"})
    if record.status != BusinessStatus.WAITING and status in (BusinessStatus.SUCCESS, BusinessStatus.FAILED):
        return render_json({'result': False, 'msg': u"设置任务状态失败！"})
    try:
        record.status = status
        record.audit_reason = audit_reason
        if status == BusinessStatus.FAILED:
            record.submit_status = SubmitStat.DEFAULT
        elif status == BusinessStatus.SUCCESS or status == BusinessStatus.WAITING:
            record.submit_status = SubmitStat.SUBMIT
        record.save()
        return render_json({'result': True, 'msg': u"设置任务状态成功！"})
    except Exception, e:
        logger.error(u"设置任务状态失败：%s, business_name:%s, template_name:%s" % (e, business_name, template_name))
        return render_json({'result': False, 'msg': u"设置任务状态失败！"})


@check_operate()
def change_stat(request):
    """
    提交审核
    """
    b_name = request.POST.get('business_name', '')
    t_name = request.POST.get('template_name', '')
    try:
        num = BusinessRecord.objects.filter(
            business_name=b_name, template_name=t_name,
        ).update(status='0', submit_status='1')
    except Exception, e:
        logger.error(u"change_stat error %s,business_name:%s,template_name:%s,user:%s" %
                     (e, b_name, t_name, request.user.username))
        return render_json({'result': False})
    return render_json({'result': True if num != 0 else False})


@check_operate()
def business_operate(request):
    """
    根据操作标识符，返回任务实例数据
    """
    template_name = request.GET.get('template_name')
    business_name = request.GET.get('business_name')
    try:
        instance = BusinessRecord.objects.get(template_name=template_name, business_name=business_name)
    except ObjectDoesNotExist:
        logger.info(u"BusinessRecord class does not exist,template_name=%s, business_name=%s" % (
            template_name, business_name))
        return render_mako_context(request, '/manager/403.html', {'result': True, 'isNotPass': True,
                                                                  'data': u"参数错误"})
    if not instance.operator.filter(username=request.user.username).exists():
        return render_mako_context(request, '403.html')
    data = get_param_data_by_name("instance", b_name=instance.business_name, t_name=instance.template_name,
                                  stat_all=False)
    json_ = {'instance': BusinessRecord.to_dict(instance), 'parm_data': data}
    return render_mako_context(request, '/task_center/some_template_play.html', json_)


@check_operate()
def check_msg(request):
    """
    长轮训检查消是否有新的动态
    """
    business_name = request.POST.get("business_name", '')
    template_name = request.POST.get("template_name", '')
    current_list = request.POST.get("current", '').split(';')
    try:
        current = []
        for i in current_list:
            if i:
                current.append(int(i))
    except Exception, e:
        logger.error(u"参数不合法：%s" % e)
        return render_json({'result': False, 'reload': False, "msg": u""})
    i = 0
    while True:
        time.sleep(1)
        x = BusinessInstanceStepDetail.objects.filter(
            ~Q(operation='0'), ~Q(stat=1), step_xh__in=current,
            business_step__business__business_name=business_name,
            business_step__business__template_name=template_name,
        )
        if x.count() > 0:
            dic_list = BusinessInstanceStepDetail.to_dict(x)
            return render_json({'result': True, 'reload': False, "msg": u"数据已更新", "dict": dic_list})
        if i == 15:
            return render_json({'result': False, 'reload': False, "msg": u""})
        i += 1
    return render_json({'result': False, 'reload': False, "msg": u""})


@check_operate()
def steps_status_get(request):
    """
    获取步骤的完成状态
    """
    template_name = request.GET.get('template_name', '')
    business_name = request.GET.get('business_name', '')
    steps = BusinessInstanceStep.objects.filter(
        business__template_name=template_name,
        business__business_name=business_name,
    ).values('name')
    data = []
    for step in steps:
        n = BusinessInstanceStepDetail.objects.filter(
            ~Q(stat=1),
            operation=DetailOperation.DEFAULT,
            business_step__business__template_name=template_name,
            business_step__business__business_name=business_name,
            business_step__name=step['name']
        ).count()
        data.append({'name': step['name'], 'flag': n > 0})
    return render_json({'result': True, 'data_list': data})


@check_operate()
@transaction.atomic()
def save_actions(request):
    form = SaveActionForm(request.POST)
    if not form.is_valid():
        return render_json({'result': False, 'msg': u"数据出错！"})
    operations = form.cleaned_data['operate']
    force_msg = form.cleaned_data['force_msg']
    business_name = form.cleaned_data['business_name']
    template_name = form.cleaned_data['template_name']

    details = operations.keys()
    steps = BusinessInstanceStep.objects.filter(business_step__step_xh__in=details,
                                                business__template_name=template_name,
                                                business__business_name=business_name,
                                                ).distinct().order_by('pk').values_list('pk', flat=True)
    if not steps:
        return render_json({'result': False, 'msg': u"数据出错！"})
    max_step = steps[len(steps) - 1]
    flag = BusinessInstanceStep.objects.filter(~Q(pk__in=steps),
                                               ~Q(business_step__stat=1),
                                               business_step__operation=DetailOperation.DEFAULT,
                                               business__template_name=template_name,
                                               business__business_name=business_name,
                                               pk__lt=max_step
                                               ).distinct().count()
    if flag > 0:
        return render_json({'result': False, 'msg': u"请先完成前面的步骤！"})
    msg = ''
    for detail_step in details:
        detail = BusinessInstanceStepDetail.objects.filter(
            ~Q(stat=Stat.DELETE),
            business_step__business__template_name=template_name,
            business_step__business__business_name=business_name,
            step_xh=int(detail_step), operation=DetailOperation.DEFAULT)
        if not detail:
            return render_json({'result': False, "msg": u"操作失败"})
        # 强制确认
        user = request.user
        if user not in detail[0].responser.all():
            confirm_info = force_msg
        else:
            confirm_info = ''
        num = detail.update(done_time=datetime.datetime.now(), confirm_info=confirm_info,
                            operation=DetailOperation.COMPLETED if operations[detail_step] else 2, confirm_user=user)
        if not num:
            msg += str(detail.step_xh) + ' '
    BusinessRecord.objects.filter(business_name=business_name, template_name=template_name).update(status='3')
    if not BusinessInstanceStepDetail.objects.filter(
            ~Q(stat=1),
            operation=0,
            business_step__business__template_name=template_name,
            business_step__business__business_name=business_name,
    ).exists():
        BusinessRecord.objects.filter(business_name=business_name, template_name=template_name).update(
            status='4')
    if not msg:
        return render_json({'result': True, "msg": u"操作成功"})
    else:
        return render_json({'result': True, "msg": u"%s序号步骤已被标记！" % msg})


def help_document(request):
    return render_mako_context(request, '/task_center/help.html')
