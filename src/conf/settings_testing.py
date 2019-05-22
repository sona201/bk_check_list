# -*- coding: utf-8 -*-
"""
用于测试环境的全局配置
"""
from settings import APP_ID
# ===============================================================================
# 数据库设置, 本地开发数据库设置
# ===============================================================================
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',  # 我们默认用mysql
#         'NAME': APP_ID,                        # 数据库名 (默认与APP_ID相同)
#         'USER': '',                            # 你的数据库user
#         'PASSWORD': '',                        # 你的数据库password
#         'HOST': '127.0.0.1',                   		   # 数据库HOST
#         'PORT': '3306',                        # 默认3306
#     },
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dbtest',  # 数据库名
        'USER': 'root',  # 数据库用户
        'PASSWORD': 'Uqv.83WuNm',  # 数据库密码
        'HOST': '10.0.1.192',  # 数据库主机
        'PORT': '3306',  # 数据库端口
    },
}