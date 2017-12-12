# -*- coding: utf-8 -*-
{
    'name': '首页设置',
    'version': '11.11',
    'author': "医伴金服",
    'summary': '首页配置',
    'category': 'Tools',
    'description':
    '''
                            该模块实现了可配置的首页系统。
    ''',
    'data': [
        'security/groups.xml',
        "views/home_page_views.xml",
        "views/home_page_action.xml",
        "views/home_page_menu.xml",
        'security/ir.model.access.csv',
    ],
    'depends': ['base', 'web', 'mail'],
    'qweb': ['static/src/xml/*.xml'],
}
