# -*- coding: utf-8 -*-
{
    'name': "客户报价管理",
    'summary': "管理客户跟进过程",
    'description':
    '''
    该模块实现了客户报价跟进过程管理的功能。
    ''',
    'author': "医伴金服",
    'website': "http://www.yibanjf.com",

    'category': 'gooderp',
    'version': '11.11',

    'depends': ['task'],

    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/crm_view.xml',
        'data/crm_data.xml',
    ],
    'application': True,
}
