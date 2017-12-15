# -*- coding: utf-8 -*-
{
    "name": "流程审批",
    "version": '11.11',
    "author": '医伴金服',
    "website": "http://www.yibanjf.com",
    "category": "gooderp",
    "description": """
    可配置的审批流程
    """,
    "data": [
        'data/data.xml',
        'views/good_process.xml',
        'security/ir.model.access.csv',
    ],
    "depends": [
        'core',
    ],
    'qweb': [
        'static/src/xml/approver.xml',
    ],
}
