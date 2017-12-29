# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models
from odoo.exceptions import UserError


class Partner(models.Model):
    '''
    业务伙伴可能是客户： c_category_id 非空
    '''
    _name = 'partner'
    _description = u'业务伙伴'
    _inherit = ['mail.thread']

    @api.model
    def _default_partner_type(self):
        '''获取默认类型'''
        return self.env.context.get('type', False)

    state = fields.Selection([
        ('draft', u'未审核'),
        ('done', u'已审核'),
        ('cancel', u'已作废')
    ], string=u'首营审核', readonly=True,
        default='draft', copy=False, index=True,
        help=u'合作伙伴首营审核状态。新建时状态为未审核;审核后状态为已审核')

    code = fields.Char(u'编号')
    name = fields.Char(u'名称', required=True, copy=False)

    main_mobile = fields.Char(u'联系电话', required=True, size=20)
    main_address = fields.Char(u'详细地址')
    fax = fields.Char(u'传真')
    postcode = fields.Char(u'邮编')

    c_category_id = fields.Many2one('core.category', u'客户类别',
                                    ondelete='restrict',
                                    domain=[('type', '=', 'customer')],
                                    context={'type': 'customer'})
    s_category_id = fields.Many2one('core.category', u'供应商类别',
                                    ondelete='restrict',
                                    domain=[('type', '=', 'supplier')],
                                    context={'type': 'supplier'})
    type = fields.Selection([
        ('MNF', u'生产企业'),
        ('SUP', u'供应商'),
        ('CUS', u'客户'),
    ], default=_default_partner_type, string=u'业务伙伴类型')

    receivable = fields.Float(u'应收余额', readonly=True,
                              digits=dp.get_precision('Amount'))
    payable = fields.Float(u'应付余额', readonly=True,
                           digits=dp.get_precision('Amount'))
    tax_num = fields.Char(u'税务登记号')
    tax_rate = fields.Float(u'税率(%)',
                            help=u'业务伙伴税率')
    bank_name = fields.Char(u'开户行')
    bank_num = fields.Char(u'银行账号')

    credit_limit = fields.Float(u'信用额度', track_visibility='onchange',
                                help=u'客户购买商品时，本次发货金额+客户应收余额要小于客户信用额度')
    active = fields.Boolean(u'启用', default=True)
    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())
    tag_ids = fields.Many2many('core.value',
                               string=u'标签',
                               domain=[('type', '=', 'partner_tag')],
                               context={'type': 'partner_tag'})
    source = fields.Char(u'来源')
    note = fields.Text(u'备注')
    main_contact = fields.Char(u'主联系人')
    responsible_id = fields.Many2one('res.users', u'负责人员', default=lambda self: self.env.user)

    onsite_check = fields.Boolean(u'需要实地考察')

    cert_ids = fields.One2many('partner.cert.info', 'partner_id', string=u'合作伙伴认证信息')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', '业务伙伴不能重名')
    ]

    @api.multi
    def partner_done(self):
        '''合作伙伴的审核按钮'''
        self.ensure_one()

        return self.write({
            'state': 'done',
        })

    @api.multi
    def partner_draft(self):
        '''合作伙伴的反审核按钮'''
        self.ensure_one()

        return self.write({
            'state': 'draft',
        })

    @api.onchange('type')
    def onchange_type(self):
        """
        :return: 根据type调整c_category_id 和 s_category_id
        """
        if self.type == 'MNF':
            self.c_category_id = None
            self.s_category_id = None
        elif self.type == 'SUP':
            self.c_category_id = None
        elif self.type == 'CUS':
            self.s_category_id = None

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        在many2one字段中支持按编号搜索
        """
        args = args or []
        if name:
            args.append(('code', 'ilike', name))
            partners = self.search(args)
            if partners:
                return partners.name_get()
            else:
                args.remove(('code', 'ilike', name))
        return super(Partner, self).name_search(name=name,
                                                args=args,
                                                operator=operator,
                                                limit=limit)

    @api.multi
    def action_view_buy_history(self):
        '''
        This function returns an action that display buy history of given sells order ids.
        Date range [180 days ago, now]
        '''
        self.ensure_one()
        date_end = datetime.today()
        date_start = datetime.strptime(self.env.user.company_id.start_date, '%Y-%m-%d')

        if (date_end - date_start).days > 365:
            date_start = date_end - timedelta(days=365)

        buy_order_track_wizard_obj = self.env['buy.order.track.wizard'].create({'date_start': date_start,
                                                                                'date_end': date_end,
                                                                                'partner_id': self.id})

        return buy_order_track_wizard_obj.button_ok()

    @api.multi
    def write(self, vals):
        # 业务伙伴应收/应付余额不为0时，不允许取消对应的客户/供应商身份
        if self.type == 'CUS' and vals.get('type') == False and self.receivable != 0:
            raise UserError(u'该客户应收余额不为0，不能取消客户类型')
        if self.type == 'SUP' and vals.get('type') == False and self.payable != 0:
            raise UserError(u'该供应商应付余额不为0，不能取消供应商类型')
        return super(Partner, self).write(vals)


class PartnerCertInfo(models.Model):
    _name = "partner.cert.info"
    _description = u"合作伙伴认证信息"
    _sort = "id desc"

    @api.one
    @api.depends('cert_expire')
    def _get_expire_status(self):
        res = 0
        if self.cert_expire:
            exp_date = datetime.strptime(self.cert_expire, '%Y-%m-%d')
            res = (date.today() - exp_date.date()).days
        self.days_to_expire = res

    partner_id = fields.Many2one('partner', u'合作伙伴', ondelete='cascade')
    partner_type = fields.Selection(
        related='partner_id.type',
        string='合作伙伴类型',
        readonly=True,
        store=False,
    )

    cert_name = fields.Many2one('core.value', u'证书名称',
                                ondelete='restrict',
                                domain=[('type', '=', 'cert_name')],
                                context={'type': 'cert_name'})
    cert_number = fields.Char(u'证书编号', required=True)
    cert_company_name = fields.Char(u'证书企业名称', required=True)
    cert_company_address = fields.Char(u'证书企业地址')
    cert_issue_date = fields.Date(u'证书发证日期', required=True)
    cert_expire = fields.Date(u'证书有效期', default=fields.Date.context_today, required=True,
                              help=u'证书有效期, 默认为当前天')
    cert_scope = fields.Char(u'许可范围')
    cert_count = fields.Integer(u'张数', default='1')

    economics_type = fields.Char(u'经济性质')
    business_type = fields.Char(u'经营方式')
    registration_amount = fields.Integer(u'注册资金')
    legal_person = fields.Char(u'法人')

    note = fields.Text(u'备注')

    days_to_expire = fields.Integer(u'过期天数', compute=_get_expire_status, readonly=True)

    _sql_constraints = [
        ('cert_number_uniq', 'unique(cert_number)', u'证书编号不能重复'),
    ]
