# -*- coding: utf-8 -*-
from ..base import ComponentAPI


class CollectionsCC(object):
    """Collections of CC APIS"""

    def __init__(self, client):
        self.client = client

        self.get_app_by_user = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_app_by_user/',
            description=u'查询用户有权限的业务',
        )
        self.get_app_host_list = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_app_host_list/',
            description=u'查询业务主机列表',
        )
        self.get_app_list = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_app_list/',
            description=u'查询业务列表',
        )
        self.get_host_list_by_ip = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_host_list_by_ip/',
            description=u'根据IP查询主机信息',
        )
        self.get_hosts_by_property = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_hosts_by_property/',
            description=u'根据 set 属性查询主机',
        )
        self.get_module_host_list = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_module_host_list/',
            description=u'查询模块主机列表',
        )
        self.get_modules = ComponentAPI(
            client=self.client, method='POST', path='/api/c/compapi/cc/get_modules/',
            description=u'查询业务下的所有模块',
        )
        self.get_modules_by_property = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_modules_by_property/',
            description=u'根据 set 属性查询模块',
        )
        self.get_set_host_list = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_set_host_list/',
            description=u'查询Set主机列表',
        )
        self.get_set_property = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_set_property/',
            description=u'获取所有 set 属性',
        )
        self.get_sets_by_property = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_sets_by_property/',
            description=u'根据 set 属性获取 set',
        )
        self.get_topo_tree_by_app_id = ComponentAPI(
            client=self.client, method='GET', path='/api/c/compapi/cc/get_topo_tree_by_app_id/',
            description=u'查询业务拓扑树',
        )
