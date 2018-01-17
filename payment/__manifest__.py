# -*- coding: utf-8 -*-

{
    'name': '支付账号配置',
    'category': 'Accounting',
    'summary': '基础支付模块',
    'version': '1.0',
    'description': """给公司添加线上支付账号""",
    'depends': ['money'],
    'data': [
        # 'data/account_data.xml',
        # 'data/payment_acquirer_data.xml',
        'views/payment_views.xml',
        # 'views/account_config_settings_views.xml',
        # 'views/account_payment_views.xml',
        # 'views/payment_templates.xml',
        # 'views/res_partner_views.xml',
        'security/ir.model.access.csv',
        'security/payment_security.xml',
    ],
    'installable': True,
    'auto_install': True,
}
