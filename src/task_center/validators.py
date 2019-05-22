# -*- coding: utf-8 -*-
from functools import wraps

from django.core.exceptions import PermissionDenied

from account.models import BkUser
from task_center.models import BusinessRecord, BusinessTemplate


def check_perm():
    """
    装饰器： 用户是否拥有调用该方法的权限
    """

    def _limits(view_func):
        @wraps(view_func)
        def _awrapper_view(request):
            user = BkUser.objects.get(username=request.user.username)
            if not user.is_staff:
                raise PermissionDenied
            return view_func(request)

        return _awrapper_view

    return _limits


def check_operate():
    """
    装饰器： 用户是否拥有可操作权限
    """

    def _limits(view_func):
        @wraps(view_func)
        def _awrapper_view(request):
            user_name = request.user.username
            args = request.GET if request.method == "GET" else request.POST
            business_name = args.get('business_name', '')
            template_name = args.get('template_name', '')
            if not (BusinessTemplate.objects.filter(
                    business_name=business_name,
                    template_name=template_name,
                    operator__username=user_name).exists() or BusinessRecord.objects.filter(
                business_name=business_name,
                template_name=template_name,
                operator__username=user_name
            ).exists()):
                raise PermissionDenied
            return view_func(request)

        return _awrapper_view

    return _limits
