# -*- coding: utf-8 -*-
from pypinyin import pinyin, Style

from odoo import models, fields, api
from odoo.exceptions import UserError


class StaffDepartment(models.Model):
    _name = "staff.department"
    _description = u'员工部门'
    _inherits = {'auxiliary.financing': 'auxiliary_id'}

    auxiliary_id = fields.Many2one(
        string=u'辅助核算',
        comodel_name='auxiliary.financing',
        ondelete='cascade',
        required=True,
    )

    pinyin_abbr = fields.Char(u'拼音简码')
    manager_id = fields.Many2one('staff', u'部门经理')
    member_ids = fields.One2many('staff', 'department_id', u'部门成员')
    parent_id = fields.Many2one('staff.department', u'上级部门')
    child_ids = fields.One2many('staff.department', 'parent_id', u'下级部门')
    note = fields.Text(u'备注')
    active = fields.Boolean(u'启用', default=True)

    @api.onchange('name')
    def onchange_name(self):
        """
        :return: 修改名称时候，生成拼音简码
        """
        if self.name:
            # 只获取首字母拼音 [['z'], ['x']]
            abbrs = pinyin(self.name, style=Style.FIRST_LETTER)
            self.pinyin_abbr = ''.join([item[0].upper() for item in abbrs])

    @api.one
    @api.constrains('parent_id')
    def _check_parent_id(self):
        '''上级部门不能选择自己和下级的部门'''
        if self.parent_id:
            staffs = self.env['staff.department'].search(
                [('parent_id', '=', self.id)])
            if self.parent_id in staffs:
                raise UserError(u'上级部门不能选择他自己或者他的下级部门')

    @api.multi
    def view_detail(self):
        for child_department in self:
            context = {'default_name': child_department.name,
                       'default_manager_id': child_department.manager_id.id,
                       'default_parent_id': child_department.parent_id.id}
            res_id = self.env['staff.department'].search(
                [('id', '=', child_department.id)])
            view_id = self.env.ref('staff.view_staff_department_form').id

            return {
                'name': u'部门/' + child_department.name,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'staff.department',
                'res_id': res_id.id,
                'view_id': False,
                'views': [(view_id, 'form')],
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current',
            }

