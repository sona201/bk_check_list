# -*- coding: utf-8 -*-
import datetime
import json
import operator as op
from collections import OrderedDict, deque
from copy import deepcopy

import requests
from django.db import transaction
from django.db.models import F, Q

import xlrd
from account.models import BkUser
from common.log import logger
from conf.default import APP_ID, APP_TOKEN, BK_PAAS_HOST
from constants import (BUSINESS_DETAIL_MODEL, BUSINESS_MODEL,
                       BUSINESS_STEP_MODEL, Stat)
from task_center.models import Application


def save_template_business(business_name, template_name, business_type, operator, user, template_data):
    with transaction.atomic():
        defaults = {'template': {'template_name': template_name, 'business_name': business_name,
                                 'business_type': business_type, 'creator': user, 'updater': user,
                                 'app': Application.objects.get(cc_name=business_name)},
                    'instance': {'template_name': template_name, 'business_name': business_name + '_v1',
                                 'business_version': "v1", 'business_type': business_type,
                                 'business_name_order': business_name, 'creator': user,
                                 'status': '0', 'submit_status': '0',
                                 'app': Application.objects.get(cc_name=business_name)}}
        templates = ['template', 'instance']
        for key in templates:
            template = BUSINESS_MODEL[key](**defaults[key])
            operator_list = string_to_users(operator)
            template.save()
            for i in operator_list:
                template.operator.add(i)
            if key == 'instance':
                for i in operator_list:
                    template.audit_user.add(i)
            template.save()

            # 保存步骤
            param = OrderedDict()
            # 步骤序号
            indexs = 1

            data_details = deepcopy(template_data)
            for one_data in data_details:
                step = one_data["step"]
                del one_data["step"], one_data["id"]
                one_data[u"step_xh"] = indexs
                if step not in param:
                    param[step] = list()
                param[step].append(one_data)
                indexs += 1
            for keys in param:
                k = param[keys]
                tempstep = BUSINESS_STEP_MODEL[key].objects.create(name=keys, business=template)

                # 保存详情
                for details in k:
                    responser_list = string_to_users(details['responser'])
                    del details['responser']
                    detail = BUSINESS_DETAIL_MODEL[key](business_step=tempstep, **details)
                    detail.save()
                    for responser in responser_list:
                        detail.responser.add(responser)
                    detail.save()


@transaction.atomic()
def check_init(username):
    if Application.objects.filter(operator__username=username).exists():
        return True
    user = BkUser.objects.get(username=username)
    app = Application.objects.get_or_create(cc_name=u"示例APP-%s" % username, cc_id=0, cc_name_abbr='')[0]
    app.operator.add(user)
    data = xlrd.open_workbook('static/file/checklist.xls')
    table = data.sheet_by_index(0)
    nrows = table.nrows
    parm_data = []
    step = ''
    step_num = 0
    rol = 0
    queue = deque([0])
    for i in range(1, nrows):
        if table.row(i)[0].value:
            step = table.row(i)[0].value
            if step_num != 0:
                queue.append(rol)
            step_num = 0
        rol += 1
        step_num += 1
        parm_data.append({
            'step': step,
            'id': rol,
            'operate_attention': table.row(i)[2].value,
            'comment': table.row(i)[3].value,
            'responser': table.row(i)[4].value,
        })
    save_template_business(u"示例APP-%s" % username, u"示例模版-%s" % username, u"变更扩容", username, user, parm_data)
    return True


def get_all_users(bk_token):
    url = BK_PAAS_HOST + '/api/c/compapi/bk_login/get_all_user/'
    request_data = {'app_code': APP_ID, 'app_secret': APP_TOKEN, 'bk_token': bk_token}
    try:
        result = requests.get(url, request_data)
        data = json.loads(result.text)['data']
        user_lists = [user['username'] for user in data]
        return user_lists
    except Exception as e:
        logger.error(u'获取用户信息失败%s' % e)
        return []


def get_param_data_by_name(types, b_name, t_name, order_by="step_xh", value=None, stat_all=True):
    business_model = BUSINESS_DETAIL_MODEL[types]
    q_list = list()
    if not stat_all:
        q_list.append((~Q(stat=1)))
    q_list.append(Q(business_step__business__business_name=b_name))
    q_list.append(Q(business_step__business__template_name=t_name))
    if value:
        q_list.append(Q(business_step__name=value))
    details = business_model.objects.filter(reduce(op.and_, q_list)).order_by(order_by)
    parm_data = OrderedDict()
    for detail in details:
        step = detail.business_step.name
        if step not in parm_data:
            parm_data[step] = list()
        dic = business_model.to_dict([detail])[0]
        parm_data[step].append(dic)
    k = parm_data.keys()
    return [(k[v], parm_data[k[v]]) for v in range(len(k))]


@transaction.atomic()
def delete_task_step(types, b_name, t_name, step_xh, name):
    business_detail = BUSINESS_DETAIL_MODEL[types]
    details = business_detail.objects.filter(business_step__business__business_name=b_name,
                                             business_step__business__template_name=t_name,
                                             business_step__business__operator__username=name,
                                             step_xh=step_xh
                                             )
    if types == "template":
        num = details.delete()
        q = Q()

    elif types == "instance":
        q = ~Q(stat=Stat.DELETE)
        num = details.update(stat=Stat.DELETE)
    else:
        return False
    if num == 0:
        return False
    flag = business_detail.objects.filter(
        q,
        business_step__business__business_name=b_name,
        business_step__business__template_name=t_name,
        business_step__business__operator__username=name,
        step_xh__gt=step_xh).update(step_xh=F("step_xh") - 1)
    return flag


@transaction.atomic()
def create_task_step(types, b_name, t_name, step_xh, name, operate_attention, comment, responser):
    business_detail = BUSINESS_DETAIL_MODEL[types]
    q = Q()
    if types == "instance":
        q = ~Q(stat=1)
    # 获取原该步骤所对应的步骤序列
    step = business_detail.objects.get(
        q,
        business_step__business__business_name=b_name,
        business_step__business__template_name=t_name,
        business_step__business__operator__username=name,
        step_xh=step_xh).business_step
    business_detail.objects.filter(
        business_step__business__business_name=b_name,
        business_step__business__template_name=t_name,
        business_step__business__operator__username=name,
        step_xh__gte=step_xh).update(step_xh=F('step_xh') + 1)
    detail = business_detail.objects.create(step_xh=step_xh,
                                            comment=comment,
                                            operate_attention=operate_attention,
                                            business_step=step,
                                            )
    if types == "instance":
        detail.stat = Stat.CREATE
    responser_list = string_to_users(responser)
    for responser in responser_list:
        detail.responser.add(responser)
    detail.save()
    return True


@transaction.atomic()
def update_task_step(types, b_name, t_name, step_xh, name, operate_attention, comment, responser):
    business_detail = BUSINESS_DETAIL_MODEL[types]
    business = BUSINESS_MODEL[types]
    q = Q()
    if types == "instance":
        q = ~Q(stat=1)
    detail_list = business_detail.objects.filter(
        q,
        business_step__business__template_name=t_name,
        business_step__business__business_name=b_name,
        business_step__business__operator__username=name,
        step_xh=step_xh).order_by('step_xh')
    if not detail_list:
        return False
    responser_list = string_to_users(responser)
    if types == "template":
        detail_list.update(operate_attention=operate_attention, comment=comment)
        business.objects.filter(business_name=b_name, template_name=t_name).update(
            updater=BkUser.objects.get(username=name), update_time=datetime.datetime.now())
    elif types == "instance":
        detail_list.update(operate_attention=operate_attention, comment=comment, stat=Stat.UPDATE)
    else:
        return False
    for detail in detail_list:
        detail.responser.clear()
        for responser in responser_list:
            detail.responser.add(responser)
        detail.save()
    return True


def check_value(value, typ):
    """
    校验函数
    """

    def check_user(users):
        """
        校验输入用户合法性，返回非法用户字符串并返回状态
        """
        user_list = users.split(';')
        all_users = BkUser.objects.all().values_list('username', flat=True).distinct()
        result = [user for user in user_list if user and user not in all_users]
        return result == [], ';'.join(result)

    def check_string(s):
        """
        校验字符串是否含不合法参数
        """
        danger = ['`', '~', '@', '#', '$', '^', '&', '*', '=', '|', '{', '}', "'", ':', '"',
                  '\\', '[', '/', ']', '<', '>', '/', '?']
        if any(i in s for i in danger):
            return False, None
        return True, None

    if value is None:
        return False, None
    if typ == 'user':
        return check_user(value)
    if typ == 'string':
        return check_string(value)
    return False, None


def check_users_from_paas(users, bk_token):
    """
    校验用户合法性
    """
    user_list = users.split(';')
    all_users = get_all_users(bk_token)
    bk_users = BkUser.objects.all().values_list('username', flat=True).distinct()
    for user in user_list:
        if user in all_users and user not in bk_users:
            BkUser.objects.create(username=user)
    result = [user for user in user_list if user and user not in all_users]
    return result == [], ';'.join(result)


def string_to_users(users):
    if users is None:
        return []
    users = users.split(';')
    user_list = BkUser.objects.filter(username__in=users)
    return user_list
