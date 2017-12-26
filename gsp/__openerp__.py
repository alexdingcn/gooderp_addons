# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.odoo.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
}
