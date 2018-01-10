# -*- coding: utf-8 -*-
{
    'name': '客户Portal',
    'author': "医伴金服",
    'category': 'Website',
    'summary': '客户账号管理',
    'version': '1.0',
    'description': """允许客户创建账号，并从shop下单""",
    'depends': [
        'website',
        'core',
    ],
    'data': [
        'views/portal_view.xml',
        'views/good_portal_templates.xml',
    ],
}
