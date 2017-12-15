# -*- coding: utf-8 -*-
{
    'name': "固定资产模块",
    'author': "医伴金服",
    'website': "www.yibanjf.com",
    'category': 'gooderp',
    'summary': '该模块实现了平均年限法的固定资产初始化，采购，变更，处理。',
    "description":
    '''
    该模块实现了平均年限法的固定资产初始化，采购，变更，处理。
    ''',
    'version': '11.11',
    'depends': ['money'],
    'data': [
        'views/asset.xml',
        'views/asset_action.xml',
        'views/asset_menu.xml',
        'data/asset_data.xml',
        'data/home_page.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'data/asset_demo.xml',
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'license': 'AGPL-3',
}
