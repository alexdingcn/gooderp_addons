# -*- coding: utf-8 -*-
from odoo import models, fields


class StaffEmployeeCategory(models.Model):
    _name = "staff.employee.category"
    _description = u'员工层级'

    name = fields.Char(u'名称')

    parent_id = fields.Many2one('staff.employee.category', u'上级标签', index=True)
    child_ids = fields.One2many('staff.employee.category', 'parent_id', u'下级标签')
    employee_ids = fields.Many2many('staff',
                                    'employee_category_rel',
                                    'category_id',
                                    'emp_id', u'员工')

    company_id = fields.Many2one('res.company',
                                 string=u'公司',
                                 change_default=True,
                                 default=lambda self: self.env['res.company']._company_default_get())
