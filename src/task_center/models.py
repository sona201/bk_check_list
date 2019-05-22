# -*- coding: utf-8 -*-
from django.db import models, transaction

from account.models import BkUser


def users_to_string(users):
    str_user = ''
    for user in users:
        str_user += user.username + ';'
    return str_user


class ApplicationManager(models.Manager):
    def query(self, cc_name, cc_name_abbr, operator, order):
        q = models.Q()
        if cc_name:
            q.add(models.Q(cc_name__icontains=cc_name), q.AND)
        if cc_name_abbr:
            q.add(models.Q(cc_name_abbr__icontains=cc_name_abbr), q.AND)
        apps = Application.objects.filter(q).order_by(order)
        if not operator:
            return apps

        q_f = models.Q()
        operator = operator.split(';')
        for i in operator:
            if i:
                q_f.add(models.Q(operator__username__icontains=i), q_f.OR)
        return apps.filter(q_f).distinct()


class BusinessTemplateManager(models.Manager):
    def query(self, username, business_name, business_type, template_name, order):
        """
        模版查询列表
        """
        q = models.Q()
        business_name_list = Application.objects.filter(operator__username=username).values_list(
            "cc_name", flat=True)
        if not business_name:
            q.add(models.Q(business_name__in=business_name_list), q.AND)
        else:
            if business_name not in business_name_list:
                return []
            q.add(models.Q(business_name=business_name), q.AND)
        if business_type:
            q.add(models.Q(business_type__icontains=business_type), q.AND)
        if template_name:
            q.add(models.Q(template_name__icontains=template_name), q.AND)
        businesses = self.filter(q).order_by(order, '-create_time')
        return businesses


class BusinessRecordManager(models.Manager):
    def query(self, username, business_name, business_type, business_version, template_name, status, order):
        """
       任务中心查询列表
        """
        q = models.Q()
        business_name_list = Application.objects.filter(operator__username=username).values_list(
            "cc_name", flat=True)
        if not business_name:
            q.add(models.Q(business_name_order__in=business_name_list), q.AND)
        else:
            if business_name not in business_name_list:
                return []
            q.add(models.Q(business_name_order=business_name), q.AND)
        if business_type:
            q.add(models.Q(business_type__icontains=business_type), q.AND)
        if business_version:
            q.add(models.Q(business_version__icontains=business_version), q.AND)
        if template_name:
            q.add(models.Q(template_name__icontains=template_name), q.AND)
        if status:
            q.add(models.Q(status=status), q.AND)
        businesses = self.filter(q).order_by(order, '-create_time').distinct()
        return businesses


class Application(models.Model):
    """
    业务
    """
    cc_id = models.IntegerField(u'cc业务编码')
    cc_name = models.CharField(u'cc业务名', max_length=30, unique=True)
    cc_name_abbr = models.CharField(u'cc业务名缩写', max_length=30, null=True, blank=True)
    operator = models.ManyToManyField(BkUser, verbose_name=u'业务可操作者')

    objects = ApplicationManager()

    def __unicode__(self):
        return self.cc_name

    class Meta:
        verbose_name = u'业务名称'
        verbose_name_plural = u'业务名称'

    def save(self, *args, **kwargs):
        if not BusinessType.objects.filter(app=self):
            DF_BUSINESS_TYPE = [u'变更扩容', u'体验服发布', u'客户端发布',
                                u'故障替换', u'开区类', u'下架类',
                                u'流程类', u'全服发布类', u'例行维护']
            with transaction.atomic():
                super(Application, self).save(*args, **kwargs)
                bt = [BusinessType(types=i, app=self) for i in DF_BUSINESS_TYPE]
                BusinessType.objects.bulk_create(bt)
                return True
        else:
            return super(Application, self).save(*args, **kwargs)

    @classmethod
    def to_dict(cls, app):
        return {
            'pk': app.pk,
            'cc_id': app.cc_id,
            'cc_name': app.cc_name,
            'cc_name_abbr': app.cc_name_abbr,
            'operator': users_to_string(app.operator.all()),
        }


class BusinessType(models.Model):
    """
    模版类型
    """
    types = models.CharField(u"模版类型", max_length=100)
    app = models.ForeignKey(Application)

    def __unicode__(self):
        return '%s %s' % (self.types, self.app.cc_name)

    class Meta:
        verbose_name = u'模版类型'
        verbose_name_plural = u'模版类型'

    @classmethod
    def to_dict(cls, details):
        data_list = []
        for detail in details:
            data_list.append({
                'cc_name': detail.app.cc_name,
                'types': detail.types,
                'id': detail.pk
            })
        return data_list


class BusinessCommon(models.Model):
    """
    任务基类
    """
    business_name = models.CharField(u"业务名称", max_length=100)
    template_name = models.CharField(u"模板名称", max_length=100)
    business_type = models.CharField(u"业务类型", max_length=20)
    operator = models.ManyToManyField(BkUser, verbose_name=u"模板可操作者", related_name='%(class)s_operator')
    creator = models.ForeignKey(BkUser, verbose_name=u"创建者", related_name='%(class)s_creator')
    create_time = models.DateTimeField(u"创建时间", auto_now_add=True)
    app = models.ForeignKey(Application, verbose_name=u'业务')

    class Meta:
        abstract = True


class BusinessDetailCommon(models.Model):
    """
    任务步骤操作事项基类
    """
    step_xh = models.IntegerField(u"步骤序号")
    operate_attention = models.TextField(u"操作事项")
    comment = models.TextField(u"备注")
    responser = models.ManyToManyField(BkUser, verbose_name=u"负责人", related_name='%(class)s_responser',blank=True)
    importance = models.BooleanField(u"是否重要", default=False)

    class Meta:
        abstract = True


class BusinessTemplate(BusinessCommon):
    """
    任务模版
    """
    updater = models.ForeignKey(BkUser, verbose_name=u"最后更新者", related_name='updater')
    update_time = models.DateTimeField(u"最后更新时间", blank=True, null=True, auto_now=True)

    objects = BusinessTemplateManager()

    def __unicode__(self):
        return '%s_%s' % (self.business_name, self.template_name)

    class Meta:
        unique_together = (("business_name", "template_name"),)
        verbose_name = u'业务模板'
        verbose_name_plural = u'业务模板'

    @classmethod
    def get_operator(cls, template):
        return users_to_string(template.operator.all())

    @classmethod
    def to_dict(cls, business):
        return {
            'id': business.pk,
            'name': business.business_name,
            'business_type': business.business_type,
            'business_name': business.business_name,
            'template_name': business.template_name,
            'operator': users_to_string(business.operator.all()),
            'creator': users_to_string([business.creator]),
            "updater": users_to_string([business.updater]),
            "create_time": business.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            "update_time": business.update_time.strftime('%Y-%m-%d %H:%M:%S') if business.update_time else '',
        }


class BusinessTemplateStep(models.Model):
    """
    任务模版详细步骤
    """
    name = models.CharField(u"步骤名称", max_length=100)
    business = models.ForeignKey(BusinessTemplate, related_name='business')

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (("name", "business"),)
        verbose_name = u'业务模版步骤'
        verbose_name_plural = u'业务模版步骤'


class BusinessTemplateStepDetail(BusinessDetailCommon):
    """
    任务模版每个步骤的操作事项
    """
    business_step = models.ForeignKey(BusinessTemplateStep, related_name='business_step')

    def __unicode__(self):
        return self.operate_attention

    class Meta:
        verbose_name = u'业务模版详细事项'
        verbose_name_plural = u'业务模版详细事项'

    @classmethod
    def to_dict(cls, details):
        details_list = []
        for detail in details:
            details_list.append({
                'step_xh': detail.step_xh,
                'operate_attention': detail.operate_attention,
                'comment': detail.comment,
                'responser': users_to_string(detail.responser.all()),
                'importance': detail.importance,
                'stat': u"默认",
                'audit_user': '',
                'submit_status': u"默认",
            })
        return details_list


class BusinessRecord(BusinessCommon):
    """
    @任务实例操作记录
    """
    business_name_order = models.CharField(u"排序用业务名称", max_length=100)
    business_version = models.CharField(u"操作识别号", max_length=50, db_index=True, blank=True, null=True)
    audit_user = models.ManyToManyField(BkUser, verbose_name=u"审核人", related_name='audit_user')
    current_step = models.IntegerField(u"当前操作步骤", default=1)
    status = models.IntegerField(u'审核结果', choices=(
        (0, u'待审核'), (1, u'审核通过'), (2, u'驳回'),
        (3, u'操作中'), (4, u'完成'), (5, u'废弃'),))
    audit_reason = models.TextField(u"审核原因", blank=True, null=True)
    submit_status = models.IntegerField(u'提交状态', choices=((0, u'未提交'), (1, u'提交')))

    objects = BusinessRecordManager()

    def __unicode__(self):
        return self.business_name

    class Meta:
        unique_together = (("business_name", "template_name"),)
        verbose_name = u'任务实例'
        verbose_name_plural = u'任务实例'

    @classmethod
    def to_dict(cls, business):
        return {'id': business.pk,
                'name': business.business_name,
                'business_type': business.business_type,
                'business_name': business.business_name.split('_')[0],
                'template_name': business.template_name,
                'business_version': business.business_version,
                'operator': users_to_string(business.operator.all()),
                'creator': users_to_string([business.creator]),
                "create_time": business.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                "current_step": business.current_step,
                'status': business.get_status_display(),
                'audit_user': users_to_string(business.audit_user.all()),
                'audit_reason': business.audit_reason,
                'submit_status': business.submit_status,
                }


class BusinessInstanceStep(models.Model):
    """
    任务实例详细步骤
    """
    name = models.CharField(u"步骤名称", max_length=100)
    business = models.ForeignKey(BusinessRecord, related_name='business')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'任务实例步骤'
        verbose_name_plural = u'任务实例步骤'


class BusinessInstanceStepDetail(BusinessDetailCommon):
    """
    实例模版每个步骤的操作事项
    """
    stat = models.IntegerField(u"状态", choices=((0, u"默认"), (1, u"删除"), (2, u"新增"), (3, u"编辑")), default=0)
    operation = models.IntegerField(u"操作", choices=((0, u"默认"), (1, u"完成"), (2, u"不涉及")),
                                    blank=True, default=0)
    confirm_info = models.TextField(blank=True, null=True)
    confirm_user = models.ForeignKey(BkUser, verbose_name=u"确认人", related_name='confirm_user', null=True, blank=True)
    done_time = models.DateTimeField(u"完成时间", blank=True, null=True)
    business_step = models.ForeignKey(BusinessInstanceStep, related_name='business_step')

    def __unicode__(self):
        return self.operate_attention

    class Meta:
        verbose_name = u'任务实例详细事项'
        verbose_name_plural = u'任务实例详细事项'

    @classmethod
    def to_dict(cls, details):
        details_list = []
        for detail in details:
            details_list.append({
                'step_xh': detail.step_xh,
                'operate_attention': detail.operate_attention,
                'comment': detail.comment,
                'responser': users_to_string(detail.responser.all()),
                'importance': detail.importance,
                'stat': detail.get_stat_display() if detail.get_stat_display() != u"默认" else '',
                'operation': detail.get_operation_display() if detail.get_operation_display() != u"默认" else '',
                'confirm_info': detail.confirm_info if detail.confirm_info else '',
                'confirm_user': users_to_string([detail.confirm_user]) if detail.confirm_user else '',
                'done_time': detail.done_time.strftime('%Y-%m-%d %H:%M:%S') if detail.done_time else '',
            })
        return details_list
