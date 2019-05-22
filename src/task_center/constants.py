# -*- coding: utf-8 -*-
from models import (BusinessInstanceStep, BusinessInstanceStepDetail,
                    BusinessRecord, BusinessTemplate, BusinessTemplateStep,
                    BusinessTemplateStepDetail)


def enum(**enums):
    return type("Enum", (), enums)

BUSINESS_DETAIL_MODEL = {'template': BusinessTemplateStepDetail, 'instance': BusinessInstanceStepDetail}
BUSINESS_MODEL = {'template': BusinessTemplate, 'instance': BusinessRecord}
BUSINESS_STEP_MODEL = {'template': BusinessTemplateStep, 'instance': BusinessInstanceStep}
STAT_LIST = [u"默认", u"删除", u"新增", u"编辑"]
OPERATION_LIST = [u"", u"完成", u"不涉及"]
Flag = enum(
    EDIT='0',
    BUSINESS='1',
    TASK='2'
)
Stat = enum(
    DEFAULT=0,
    DELETE=1,
    CREATE=2,
    UPDATE=3
)
SubmitStat = enum(
    DEFAULT=0,
    SUBMIT=1
)
HeadList = enum(
    TEMPLATE=[u"步骤类别", u"步骤序号", u"操作事项", u"备注", u"责任人"],
    INSTANCE=[u"步骤类别", u"步骤序号", u"操作事项", u"备注", u"责任人", u"完成时间", u"确认人", u"确认"]
)
ExcelList = enum(
    TEMPLATE=['step_xh', 'operate_attention', 'comment', 'responser'],
    INSTANCE=['step_xh', 'operate_attention', 'comment', 'responser', 'done_time', 'confirm_user', 'operation']
)
BusinessStatus = enum(
    WAITING=0,
    SUCCESS=1,
    FAILED=2,
    OPERATING=3,
    COMPLETED=4,
    SCRAP=5
)

DetailOperation = enum(
    DEFAULT=0,
    COMPLETED=1,
    DELETE=2
)
