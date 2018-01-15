# -*- coding: utf-8 -*-
{
    "name": "GSP管理",
    "version": '1.0',
    "author": 'AlexDing',
    "website": "http://www.yibanjf.com",
    "category": "gooderp",
    "depends": ['core', 'buy', 'goods', 'warehouse'],
    "description":
    '''
         该模块定义了GSP的采购、仓库、养护、销售功能。
    ''',
    "data": [
        'security/groups.xml',
        'view/gsp_view.xml',
        'view/goods_maintenance_view.xml',
        'action/gsp_action.xml',
        'menu/gsp_menu.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    "active": False,
    'qweb': [
        'static/src/xml/client_action.xml'
    ]
}
