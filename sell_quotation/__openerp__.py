# -*- coding: utf-8 -*-
{
    'name': "销售报价模块",
    'author': "医伴金服",
    'website': "http://www.yibanjf.com",
    'category': 'gooderp',
    'summary': 'GoodERP报价单',
    "description":
        '''
        该模块实现了给客户报价的功能。
        ''',
    'version': '11.11',
    'application': True,
    'depends': ['sell', 'good_crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/sell_quotation_view.xml',
        'data/sell_quotation_data.xml',
    ],
    'demo': [
        'data/demo.xml',
    ]
}
