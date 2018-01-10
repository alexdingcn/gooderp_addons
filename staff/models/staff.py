# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Staff(models.Model):
    _inherit = 'staff'
    _inherits = {'auxiliary.financing': 'auxiliary_id'}

    @api.onchange('user_id')
    def onchange_user_id(self):
        '''选择用户的时候带出name和phone'''
        if not self.user_id:
            return
        user = self.env['res.users'].search([('id', '=', self.user_id.id)])
        if not user:
            raise UserError(u'该用户不存在')
        else:
            user.ensure_one()

        partner = self.env['res.partner'].search([('id', '=', user.partner_id.id)])
        if not partner:
            raise UserError(u'该用户不存在')
        self.work_mobile = partner.mobile
        self.work_phone = partner.phone
        self.work_email = partner.email
        self.name = partner.name

    auxiliary_id = fields.Many2one(
        string=u'辅助核算',
        comodel_name='auxiliary.financing',
        ondelete='restrict',
        required=True,
    )
    category_ids = fields.Many2many('staff.employee.category',
                                    'employee_category_rel',
                                    'emp_id',
                                    'category_id', u'标签')
    work_mobile = fields.Char(u'办公手机')
    work_email = fields.Char(u'办公邮箱')
    work_phone = fields.Char(u'办公电话')
    image_medium = fields.Binary(string=u'头像', related="user_id.image", attachment=True,
                                 readonly=True, store=False)
    # 个人信息
    birthday = fields.Date(u'生日')
    identification_id = fields.Char(u'证照号码')
    is_arbeitnehmer = fields.Boolean(u'是否雇员', default='1')
    is_investoren = fields.Boolean(u'是否投资者')
    is_bsw = fields.Boolean(u'是否残疾烈属孤老')
    type_of_certification = fields.Selection([
        ('ID', u'居民身份证'),
        ('Military_ID', u'军官证'),
        ('Soldiers_Card', u'士兵证'),
        ('Police_badge', u'武警警官证'),
        ('Passport_card', u'护照'),
    ],
        u'证照类型',
        default='ID',
        required=True)
    gender = fields.Selection([
        ('male', u'男'),
        ('female', u'女')
    ], u'性别')
    marital = fields.Selection([
        ('single', u'单身'),
        ('married', u'已婚'),
        ('widower', u'丧偶'),
        ('divorced', u'离异')
    ], u'婚姻状况')
    contract_ids = fields.One2many('staff.contract', 'staff_id', u'合同')
    active = fields.Boolean(u'启用', default=True)
    # 公开信息

    department_id = fields.Many2one('staff.department', u'部门')
    parent_id = fields.Many2one('staff', u'部门经理')
    notes = fields.Text(u'其他信息')
    emergency_contact = fields.Char(u'紧急联系人')
    emergency_call = fields.Char(u'紧急联系方式')
    bank_name = fields.Char(u'开户行')
    bank_num = fields.Char(u'银行账号')

    @api.model
    def staff_contract_over_date(self):
        # 员工合同到期，发送邮件给员工 和 部门经理（如果存在）
        now = datetime.now().strftime("%Y-%m-%d")
        for Staff in self.search([]):
            if not Staff.contract_ids:
                continue

            for contract in Staff.contract_ids:
                if now == contract.over_date:
                    self.env.ref('staff.contract_over_due_date_employee').send_mail(
                        self.env.user.id)
                    if Staff.parent_id and Staff.parent_id.work_email:
                        self.env.ref('staff.contract_over_due_date_manager').send_mail(
                            self.env.user.id)

        return




